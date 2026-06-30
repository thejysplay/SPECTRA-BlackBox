#!/usr/bin/env python3
"""SPECTRA-BlackBox P1 — 수집 어댑터 (P1_DESIGN v2 §3-A). [구현 1단계, self-contained]

목적: 대상 에이전트와의 상호작용을 추상화한다. 인스펙터는 대상이 streamlit/API/CLI든
AgentAdapter 인터페이스로만 보고, 관측은 RawObservation으로 표준화된다.
→ critic-1(과적합) 해소: 수집층이 더는 단일 아키텍처(streamlit/ReAct)에 하드코딩되지 않는다.

핵심 분리:
  - AgentAdapter.send(msg) -> RawObservation   (transport 추상)
  - StepExtractor (plug-in)                     (도구단계 포맷: ReAct/tool_calls/opaque)
  - observation_tier 1급                         (불투명 대상도 빈손 아니라 T0로 명시)

구현체: StreamlitAdapter (현 DVLA). 향후 APIAdapter / CLIAdapter 추가.
streamlit 전용 로직(셀렉터·완료대기·캡처)은 StreamlitAdapter 영역에만 격리.
"""

from __future__ import annotations

import json
import re
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from playwright.sync_api import sync_playwright


# ─────────────────────────────────────────────────────────────
# 표준 관측 (대상 아키텍처 무관)
# ─────────────────────────────────────────────────────────────
@dataclass
class RawObservation:
    visible_text: str                       # 사용자에게 보이는 응답
    disclosed_steps: list                   # 노출된 도구 단계 [{action, action_input}] 또는 []
    disclosure_format: str                  # "react" | "openai_tool_calls" | "xml" | "opaque"
    observation_tier: str                   # T0(불투명) | T1(도구단계 노출) | T2(승인UI·side-effect)
    raw_panels: list = field(default_factory=list)   # 원본 패널 텍스트(디버그/재추출용)
    side_channels: dict = field(default_factory=dict)


# ─────────────────────────────────────────────────────────────
# StepExtractor — 도구 단계 포맷 plug-in (critic-1: ReAct 가정 제거)
#   extract() 반환: 단계 리스트(이 포맷 맞음) 또는 None(이 포맷 아님 → 다음 추출기)
# ─────────────────────────────────────────────────────────────
class StepExtractor(ABC):
    name: str = "base"

    @abstractmethod
    def extract(self, text: str) -> list | None: ...


class ReActJSONExtractor(StepExtractor):
    """langchain ReAct: {"action": "...", "action_input": ...} 블록."""
    name = "react"
    _PAT = re.compile(r'\{[^{}]*?"action"\s*:.*?\}', re.S)

    def extract(self, text: str) -> list | None:
        out, seen = [], set()
        for m in self._PAT.finditer(text or ""):
            try:
                o = json.loads(m.group(0))
            except Exception:
                continue
            if not (isinstance(o, dict) and "action" in o):
                continue
            if str(o.get("action", "")).lower() == "final answer":
                continue
            key = (str(o.get("action")),
                   json.dumps(o.get("action_input"), ensure_ascii=False, sort_keys=True))
            if key in seen:
                continue
            seen.add(key)
            out.append({"action": str(o.get("action", "")), "action_input": o.get("action_input")})
        return out if out else None   # action 블록 자체가 없으면 이 포맷 아님


class OpenAIToolCallExtractor(StepExtractor):
    """OpenAI tool_calls — 향후 APIAdapter가 구조적으로 채움. 텍스트 경로는 미지원."""
    name = "openai_tool_calls"

    def extract(self, text: str) -> list | None:
        return None


class OpaqueExtractor(StepExtractor):
    """최종 fallback — 도구 단계가 안 보이는 불투명 대상. 항상 빈 단계(명시적 '없음')."""
    name = "opaque"

    def extract(self, text: str) -> list | None:
        return []


DEFAULT_EXTRACTORS: list[StepExtractor] = [
    ReActJSONExtractor(), OpenAIToolCallExtractor(), OpaqueExtractor()
]


def run_extractors(text: str, extractors: list[StepExtractor] | None = None) -> tuple[list, str]:
    """추출기를 순서대로 시도, 첫 성공(None 아님) 채택. 전부 실패 시 opaque."""
    for ex in (extractors or DEFAULT_EXTRACTORS):
        r = ex.extract(text)
        if r is not None:
            return r, ex.name
    return [], "opaque"


# ─────────────────────────────────────────────────────────────
# AgentAdapter — transport 추상 인터페이스
# ─────────────────────────────────────────────────────────────
class AgentAdapter(ABC):
    @abstractmethod
    def send(self, message: str) -> RawObservation: ...

    def reset(self) -> None:
        """세션 초기화(대화 맥락 비움). fresh 수집용. 미지원 어댑터는 no-op."""
        return None

    def __enter__(self): return self
    def __exit__(self, *exc): return False


# ── streamlit UI 전용 로직 (StreamlitAdapter 영역에만 격리) ──
_ST = {
    "MSG": '[data-testid="stChatMessage"]',
    "INPUT": 'textarea[data-testid="stChatInputTextArea"]',
    "EXPANDER": '[data-testid="stExpander"]',
    "STATUS": '[data-testid="stStatusWidget"]',
}


def _st_wait_for_response(page, n_before: int, timeout: float = 90.0) -> None:
    """새 메시지가 나타나고 텍스트가 3회 연속 안정 + Running 위젯 비활성까지 대기."""
    deadline = time.monotonic() + timeout
    last_text, stable, appeared = None, 0, False
    while time.monotonic() < deadline:
        if page.locator(_ST["MSG"]).count() > n_before:
            appeared = True
            try:
                cur = page.locator(_ST["MSG"]).last.inner_text(timeout=2000)
            except Exception:
                page.wait_for_timeout(800); continue
            running = page.locator(_ST["STATUS"]).count() > 0
            if cur == last_text and not running:
                stable += 1
                if stable >= 3:
                    return
            else:
                stable, last_text = 0, cur
        page.wait_for_timeout(800)
    if not appeared:
        raise TimeoutError("응답 메시지가 나타나지 않음")


def _st_capture_last(page) -> dict:
    """마지막 메시지 + expander(도구단계) 캡처. expander는 펼쳐서 내부까지 읽는다."""
    last = page.locator(_ST["MSG"]).last
    exps = last.locator(_ST["EXPANDER"])
    for i in range(exps.count()):
        try:
            s = exps.nth(i).locator("summary")
            if s.count():
                s.first.click(timeout=1500)
                page.wait_for_timeout(200)
        except Exception:
            pass
    panels = []
    for i in range(exps.count()):
        try:
            panels.append(exps.nth(i).inner_text())
        except Exception:
            pass
    return {"response_text": last.inner_text(), "intermediate": panels}


_UI_NOISE = re.compile(
    r'^\s*(smart_toy|keyboard_arrow_down|content_copy|✅ Complete!|thumb_up|thumb_down)\s*$', re.M)
_ACTION_BLOCK = re.compile(r'\{[^{}]*?"action"\s*:.*?\}', re.S)


def _clean_visible(raw: str) -> str:
    """streamlit UI 토큰·ReAct JSON 래퍼 제거 → 사용자에게 실제 보이는 응답만 남김.
    도구 단계는 disclosed_steps로 이미 추출되므로 visible_text에선 뺀다(원문은 raw_panels에 보존)."""
    t = _UI_NOISE.sub('', raw or '')
    t = _ACTION_BLOCK.sub('', t)
    return re.sub(r'\n{2,}', '\n', t).strip()


class StreamlitAdapter(AgentAdapter):
    """streamlit 챗 UI 대상 (현 DVLA). streamlit 종속은 전부 이 클래스 안에만."""

    def __init__(self, url: str = "http://localhost:5501", headless: bool = True,
                 extractors: list[StepExtractor] | None = None):
        self.url = url
        self.headless = headless
        self.extractors = extractors or DEFAULT_EXTRACTORS
        self._pw = self._browser = self.page = None

    def __enter__(self):
        self._pw = sync_playwright().start()
        self._browser = self._pw.chromium.launch(headless=self.headless)
        self.page = self._browser.new_page()
        self.page.goto(self.url, wait_until="networkidle", timeout=30000)
        return self

    def __exit__(self, *exc):
        try:
            if self._browser:
                self._browser.close()
        finally:
            if self._pw:
                self._pw.stop()
        return False

    def reset(self) -> None:
        """페이지 리로드 = streamlit 새 세션(대화 맥락 비움)."""
        self.page.goto(self.url, wait_until="networkidle", timeout=30000)

    def send(self, message: str) -> RawObservation:
        page = self.page
        n_before = page.locator(_ST["MSG"]).count()
        box = page.locator(_ST["INPUT"])
        box.click(); box.fill(message); box.press("Enter")
        _st_wait_for_response(page, n_before)
        cap = _st_capture_last(page)
        text = cap.get("response_text", "") or ""
        panels = cap.get("intermediate", []) or []
        steps, fmt = run_extractors(text + "\n" + "\n".join(panels), self.extractors)   # 추출은 raw에서
        tier = "T1" if steps else "T0"   # T2(승인UI/부수효과)는 후속 단계
        return RawObservation(visible_text=_clean_visible(text), disclosed_steps=steps,
                              disclosure_format=fmt, observation_tier=tier, raw_panels=panels)


class APIAdapter(AgentAdapter):
    """OpenAI 호환 /v1/chat/completions 대상 (DVMN 등). streamlit 종속 없음.
    stateless API라 messages 히스토리를 직접 관리해 멀티턴 구현. reset=히스토리 비움.
    도구단계는 응답의 구조적 tool_calls에서 직접 추출(OpenAI 형식)."""

    def __init__(self, url: str, model: str = "gemini-2.5-flash",
                 headless: bool = True, extractors=None, timeout: float = 60.0):
        self.url = url                      # 예: http://localhost:7003/v1/chat/completions
        self.model = model
        self.timeout = timeout
        self.messages: list = []

    def reset(self) -> None:
        self.messages = []

    def send(self, message: str) -> RawObservation:
        import urllib.request
        self.messages.append({"role": "user", "content": message})
        body = json.dumps({"model": self.model, "messages": self.messages}).encode("utf-8")
        req = urllib.request.Request(self.url, data=body,
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=self.timeout) as r:
            data = json.loads(r.read().decode("utf-8"))
        msg = (data.get("choices") or [{}])[0].get("message", {}) or {}
        content = msg.get("content") or ""
        tool_calls = msg.get("tool_calls") or []
        self.messages.append({"role": "assistant", "content": content})   # 멀티턴 누적
        steps = [{"action": (tc.get("function") or {}).get("name"),
                  "action_input": (tc.get("function") or {}).get("arguments")}
                 for tc in tool_calls]
        fmt = "openai_tool_calls" if steps else "opaque"
        tier = "T1" if steps else "T0"
        return RawObservation(visible_text=content, disclosed_steps=steps,
                              disclosure_format=fmt, observation_tier=tier,
                              raw_panels=[], side_channels={"raw_response": data})


def make_adapter(url: str, headless: bool = True, model: str = "gemini-2.5-flash") -> AgentAdapter:
    """url로 어댑터 자동 선택: /chat/completions(OpenAI 호환 API) → APIAdapter, 그 외 → StreamlitAdapter."""
    if "/chat/completions" in url or "/v1/" in url:
        return APIAdapter(url, model=model, headless=headless)
    return StreamlitAdapter(url, headless=headless)


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://localhost:5501")
    ap.add_argument("--message", default="What are my recent transactions?")
    args = ap.parse_args()
    with StreamlitAdapter(args.url) as ad:
        obs = ad.send(args.message)
        print(json.dumps({
            "tier": obs.observation_tier, "format": obs.disclosure_format,
            "disclosed_steps": obs.disclosed_steps,
            "visible_text_head": obs.visible_text[:160],
        }, ensure_ascii=False, indent=2))
