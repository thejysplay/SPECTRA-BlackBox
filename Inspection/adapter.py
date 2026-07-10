#!/usr/bin/env python3
"""SPECTRA-BlackBox P1 — 수집 어댑터 (P1_DESIGN v2 §3-A).

목적:
- 대상 에이전트와의 상호작용을 AgentAdapter 인터페이스로 추상화
- 관측 결과는 RawObservation으로 표준화
- Streamlit / API / MCP / A2A / Goover 상용 BlackBox UI를 동일 인터페이스로 수집

핵심:
  - AgentAdapter.send(msg) -> RawObservation
  - StepExtractor plug-in
  - observation_tier: T0 | T1 | T2
"""

from __future__ import annotations

import json
import re
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from playwright.sync_api import sync_playwright


# ─────────────────────────────────────────────────────────────
# Optional commercial adapter imports
# ─────────────────────────────────────────────────────────────
try:
    # 같은 Inspection/ 폴더 안에 goover_smoke.py가 있어야 함
    from goover_smoke import GooverSmokeAdapter
except Exception:
    GooverSmokeAdapter = None

try:
    # Genspark 슈퍼에이전트 (headed/Xvfb 필수)
    from genspark_agent import GensparkAgentAdapter
except Exception:
    GensparkAgentAdapter = None

try:
    # Manus 에이전트 (headed/Xvfb 필수)
    from manus_agent import ManusAgentAdapter
except Exception:
    ManusAgentAdapter = None


# ─────────────────────────────────────────────────────────────
# 표준 관측
# ─────────────────────────────────────────────────────────────
@dataclass
class RawObservation:
    visible_text: str
    disclosed_steps: list
    disclosure_format: str
    observation_tier: str
    raw_panels: list = field(default_factory=list)
    side_channels: dict = field(default_factory=dict)


# ─────────────────────────────────────────────────────────────
# StepExtractor
# ─────────────────────────────────────────────────────────────
class StepExtractor(ABC):
    name: str = "base"

    @abstractmethod
    def extract(self, text: str) -> list | None:
        ...


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

            key = (
                str(o.get("action")),
                json.dumps(
                    o.get("action_input"),
                    ensure_ascii=False,
                    sort_keys=True,
                ),
            )

            if key in seen:
                continue

            seen.add(key)
            out.append(
                {
                    "action": str(o.get("action", "")),
                    "action_input": o.get("action_input"),
                }
            )

        return out if out else None


class OpenAIToolCallExtractor(StepExtractor):
    """OpenAI tool_calls — APIAdapter가 구조적으로 채움."""
    name = "openai_tool_calls"

    def extract(self, text: str) -> list | None:
        return None


class OpaqueExtractor(StepExtractor):
    """최종 fallback — 도구 단계가 안 보이는 불투명 대상."""
    name = "opaque"

    def extract(self, text: str) -> list | None:
        return []


DEFAULT_EXTRACTORS: list[StepExtractor] = [
    ReActJSONExtractor(),
    OpenAIToolCallExtractor(),
    OpaqueExtractor(),
]


def run_extractors(
    text: str,
    extractors: list[StepExtractor] | None = None,
) -> tuple[list, str]:
    """추출기를 순서대로 시도하고 첫 성공(None 아님)을 채택."""
    for ex in extractors or DEFAULT_EXTRACTORS:
        r = ex.extract(text)
        if r is not None:
            return r, ex.name

    return [], "opaque"


# ─────────────────────────────────────────────────────────────
# AgentAdapter
# ─────────────────────────────────────────────────────────────
class AgentAdapter(ABC):
    @abstractmethod
    def send(self, message: str) -> RawObservation:
        ...

    def reset(self) -> None:
        """세션 초기화. 미지원 어댑터는 no-op."""
        return None

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


# ─────────────────────────────────────────────────────────────
# StreamlitAdapter
# ─────────────────────────────────────────────────────────────
_ST = {
    "MSG": '[data-testid="stChatMessage"]',
    "INPUT": 'textarea[data-testid="stChatInputTextArea"]',
    "EXPANDER": '[data-testid="stExpander"]',
    "STATUS": '[data-testid="stStatusWidget"]',
}


def _st_wait_for_response(page, n_before: int, timeout: float = 90.0) -> None:
    """새 메시지 등장 + 텍스트 안정화 + Running 위젯 비활성 대기."""
    deadline = time.monotonic() + timeout
    last_text, stable, appeared = None, 0, False

    while time.monotonic() < deadline:
        if page.locator(_ST["MSG"]).count() > n_before:
            appeared = True

            try:
                cur = page.locator(_ST["MSG"]).last.inner_text(timeout=2000)
            except Exception:
                page.wait_for_timeout(800)
                continue

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
    """마지막 메시지와 expander 내부 텍스트 캡처."""
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

    return {
        "response_text": last.inner_text(),
        "intermediate": panels,
    }


_UI_NOISE = re.compile(
    r"^\s*(smart_toy|keyboard_arrow_down|content_copy|✅ Complete!|thumb_up|thumb_down)\s*$",
    re.M,
)
_ACTION_BLOCK = re.compile(r'\{[^{}]*?"action"\s*:.*?\}', re.S)


def _clean_visible(raw: str) -> str:
    """streamlit UI 토큰·ReAct JSON 래퍼 제거."""
    t = _UI_NOISE.sub("", raw or "")
    t = _ACTION_BLOCK.sub("", t)
    return re.sub(r"\n{2,}", "\n", t).strip()


class StreamlitAdapter(AgentAdapter):
    """Streamlit 챗 UI 대상."""

    def __init__(
        self,
        url: str = "http://localhost:5501",
        headless: bool = True,
        extractors: list[StepExtractor] | None = None,
    ):
        self.url = url
        self.headless = headless
        self.extractors = extractors or DEFAULT_EXTRACTORS
        self._pw = None
        self._browser = None
        self.page = None

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
        self.page.goto(self.url, wait_until="networkidle", timeout=30000)

    def send(self, message: str) -> RawObservation:
        page = self.page
        n_before = page.locator(_ST["MSG"]).count()

        box = page.locator(_ST["INPUT"])
        box.click()
        box.fill(message)
        box.press("Enter")

        _st_wait_for_response(page, n_before)
        cap = _st_capture_last(page)

        text = cap.get("response_text", "") or ""
        panels = cap.get("intermediate", []) or []

        steps, fmt = run_extractors(
            text + "\n" + "\n".join(panels),
            self.extractors,
        )

        tier = "T1" if steps else "T0"

        return RawObservation(
            visible_text=_clean_visible(text),
            disclosed_steps=steps,
            disclosure_format=fmt,
            observation_tier=tier,
            raw_panels=panels,
            side_channels={},
        )


# ─────────────────────────────────────────────────────────────
# APIAdapter
# ─────────────────────────────────────────────────────────────
class APIAdapter(AgentAdapter):
    """OpenAI 호환 /v1/chat/completions 대상."""

    def __init__(
        self,
        url: str,
        model: str = "gemini-2.5-flash",
        headless: bool = True,
        extractors=None,
        timeout: float = 60.0,
    ):
        self.url = url
        self.model = model
        self.timeout = timeout
        self.messages: list = []

    def reset(self) -> None:
        self.messages = []

    def send(self, message: str) -> RawObservation:
        import urllib.request

        self.messages.append({"role": "user", "content": message})

        body = json.dumps(
            {
                "model": self.model,
                "messages": self.messages,
            }
        ).encode("utf-8")

        req = urllib.request.Request(
            self.url,
            data=body,
            headers={"Content-Type": "application/json"},
        )

        with urllib.request.urlopen(req, timeout=self.timeout) as r:
            data = json.loads(r.read().decode("utf-8"))

        msg = (data.get("choices") or [{}])[0].get("message", {}) or {}
        content = msg.get("content") or ""
        tool_calls = msg.get("tool_calls") or []

        self.messages.append(
            {
                "role": "assistant",
                "content": content,
            }
        )

        steps = [
            {
                "action": (tc.get("function") or {}).get("name"),
                "action_input": (tc.get("function") or {}).get("arguments"),
            }
            for tc in tool_calls
        ]

        fmt = "openai_tool_calls" if steps else "opaque"
        tier = "T1" if steps else "T0"

        return RawObservation(
            visible_text=content,
            disclosed_steps=steps,
            disclosure_format=fmt,
            observation_tier=tier,
            raw_panels=[],
            side_channels={"raw_response": data},
        )


# ─────────────────────────────────────────────────────────────
# JSON RPC helper
# ─────────────────────────────────────────────────────────────
def _rpc_post(url: str, body: dict, timeout: float = 8.0) -> dict:
    import urllib.request

    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception as e:
        return {"_error": str(e)}


# ─────────────────────────────────────────────────────────────
# MCPAdapter
# ─────────────────────────────────────────────────────────────
class MCPAdapter(AgentAdapter):
    """MCP JSON-RPC tool 서버 대상."""

    def __init__(
        self,
        url: str,
        headless: bool = True,
        model: str = "",
        extractors=None,
        timeout: float = 8.0,
    ):
        self.url = url
        self.timeout = timeout

    def send(self, message: str) -> RawObservation:
        try:
            call = json.loads(message)
        except Exception:
            call = {"tool": message, "args": {}}

        tool = call.get("tool", "")
        args = call.get("args", {})

        r = _rpc_post(
            self.url,
            {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": tool,
                    "arguments": args,
                },
                "id": 1,
            },
            self.timeout,
        )

        res = (r or {}).get("result")

        if isinstance(res, dict) and "content" in res:
            text = " ".join(
                c.get("text", "") if isinstance(c, dict) else str(c)
                for c in res["content"]
            )
        elif res is not None:
            text = json.dumps(res, ensure_ascii=False)
        else:
            text = json.dumps(r, ensure_ascii=False)

        steps = [
            {
                "action": tool,
                "action_input": json.dumps(args, ensure_ascii=False),
            }
        ]

        return RawObservation(
            visible_text=text,
            disclosed_steps=steps,
            disclosure_format="mcp_tool_call",
            observation_tier="T1",
            raw_panels=[],
            side_channels={"raw": r},
        )


# ─────────────────────────────────────────────────────────────
# A2AAdapter
# ─────────────────────────────────────────────────────────────
class A2AAdapter(AgentAdapter):
    """A2A 대상."""

    def __init__(
        self,
        url: str,
        headless: bool = True,
        model: str = "",
        extractors=None,
        timeout: float = 8.0,
    ):
        self.url = url
        self.timeout = timeout

    def send(self, message: str) -> RawObservation:
        try:
            m = json.loads(message)
        except Exception:
            m = {
                "from": "agent",
                "content": message,
            }

        r = _rpc_post(
            self.url,
            {
                "from": m.get("from", "agent"),
                "to": m.get("to", "agent"),
                "content": m.get("content", ""),
            },
            self.timeout,
        )

        status = (r or {}).get("status", "")
        text = f"[{status}] {(r or {}).get('content', '')} {(r or {}).get('note', '')}".strip()

        steps = [
            {
                "action": "a2a_delegate",
                "action_input": m.get("from", ""),
            }
        ]

        return RawObservation(
            visible_text=text,
            disclosed_steps=steps,
            disclosure_format="a2a_message",
            observation_tier="T1",
            raw_panels=[],
            side_channels={"raw": r},
        )


# ─────────────────────────────────────────────────────────────
# GooverAdapter
# ─────────────────────────────────────────────────────────────
class GooverAdapter(AgentAdapter):
    """
    Goover 상용 BlackBox UI 어댑터.

    goover_smoke.py의 GooverSmokeAdapter를 SPECTRA AgentAdapter 인터페이스로 감싼다.

    특징:
    - 내부 tool call은 관측 불가
    - disclosed_steps=[]
    - disclosure_format='opaque_browser_ui'
    - observation_tier='T0'
    - evidence는 side_channels에 저장
      - source_like_links
      - source_count
      - screenshot
      - full_body_text
    """

    def __init__(
        self,
        url: str = "https://goover.ai/",
        headless: bool = True,
        model: str = "",
        extractors=None,
        timeout: float = 240.0,
        user_data_dir: str = ".spectra_sessions/goover",
        screenshot_dir: str = "goover_shots",
    ):
        if GooverSmokeAdapter is None:
            raise ImportError(
                "GooverSmokeAdapter를 import하지 못했습니다. "
                "Inspection/goover_smoke.py 파일이 adapter.py와 같은 폴더에 있는지 확인하세요."
            )

        self.url = url
        self.headless = headless
        self.timeout = timeout
        self.user_data_dir = user_data_dir
        self.screenshot_dir = screenshot_dir
        self._inner = None

    def __enter__(self):
        self._inner = GooverSmokeAdapter(
            url=self.url,
            headless=self.headless,
            user_data_dir=self.user_data_dir,
            screenshot_dir=self.screenshot_dir,
            timeout_ms=int(self.timeout * 1000),
        )

        self._inner.__enter__()
        return self

    def __exit__(self, *exc):
        if self._inner:
            return self._inner.__exit__(*exc)

        return False

    def reset(self) -> None:
        """
        P1 fresh 수집 시 probe 사이에 Goover 시작 화면으로 되돌린다.
        """
        if self._inner and hasattr(self._inner, "reset"):
            self._inner.reset()

    def send(self, message: str) -> RawObservation:
        obs = self._inner.send(message)

        return RawObservation(
            visible_text=getattr(obs, "visible_text", ""),
            disclosed_steps=[],
            disclosure_format="opaque_browser_ui",
            observation_tier="T0",
            raw_panels=getattr(obs, "raw_panels", []),
            side_channels=getattr(obs, "side_channels", {}),
        )


class GensparkAdapter(AgentAdapter):
    """
    Genspark 슈퍼 에이전트 BlackBox UI 어댑터.

    genspark_agent.py의 GensparkAgentAdapter를 SPECTRA AgentAdapter로 감싼다.

    ⚠️ Genspark은 headless 브라우저의 슈퍼에이전트 실행을 차단하므로
       **항상 headed로 강제**한다. 서버에선 Xvfb 가상화면 + DISPLAY 필요
       (run_fleet_genspark.sh 가 세팅). 로그인 세션은 프로필 재사용.

    특징: 내부 tool call 관측 불가 → disclosed_steps=[], opaque_browser_ui, T0.
          evidence는 side_channels(conversation_url/links/screenshot/full_body_text).
    """

    def __init__(
        self,
        url: str = "https://www.genspark.ai/",
        headless: bool = True,       # 무시됨 — 항상 headed 강제
        model: str = "",
        extractors=None,
        timeout: float = 300.0,
        user_data_dir: str = ".spectra_sessions/genspark",
        screenshot_dir: str = "genspark_shots",
    ):
        if GensparkAgentAdapter is None:
            raise ImportError(
                "GensparkAgentAdapter를 import하지 못했습니다. "
                "Inspection/genspark_agent.py가 adapter.py와 같은 폴더에 있는지 확인하세요."
            )
        self.url = url
        self.timeout = timeout
        self.user_data_dir = user_data_dir
        self.screenshot_dir = screenshot_dir
        self._inner = None

    def __enter__(self):
        import os
        if not os.environ.get("DISPLAY"):
            raise RuntimeError(
                "Genspark은 headed 실행이 필요합니다(headless 차단). DISPLAY가 없습니다. "
                "run_fleet_genspark.sh로 실행하거나 Xvfb(:99) 후 DISPLAY=:99를 설정하세요."
            )
        self._inner = GensparkAgentAdapter(
            user_data_dir=self.user_data_dir,
            screenshot_dir=self.screenshot_dir,
            headless=False,                       # 항상 headed
            timeout_s=int(self.timeout),
        )
        self._inner.__enter__()
        return self

    def __exit__(self, *exc):
        if self._inner:
            return self._inner.__exit__(*exc)
        return False

    def reset(self) -> None:
        if self._inner and hasattr(self._inner, "reset"):
            self._inner.reset()

    def send(self, message: str) -> RawObservation:
        obs = self._inner.send(message)
        return RawObservation(
            visible_text=getattr(obs, "visible_text", ""),
            disclosed_steps=[],
            disclosure_format="opaque_browser_ui",
            observation_tier="T0",
            raw_panels=getattr(obs, "raw_panels", []),
            side_channels=getattr(obs, "side_channels", {}),
        )


class ManusAdapter(AgentAdapter):
    """
    Manus(마누스) 에이전트 BlackBox UI 어댑터.

    manus_agent.py의 ManusAgentAdapter를 SPECTRA AgentAdapter로 감싼다.
    ⚠️ 항상 headed 강제(Cloudflare Turnstile/헤드리스 차단). Xvfb + DISPLAY 필요.
    자율 에이전트라 작업이 길다 → timeout 크게(기본 600s).
    """

    def __init__(self, url="https://manus.im/app", headless=True, model="",
                 extractors=None, timeout: float = 600.0,
                 user_data_dir=".spectra_sessions/manus", screenshot_dir="manus_shots"):
        if ManusAgentAdapter is None:
            raise ImportError(
                "ManusAgentAdapter를 import하지 못했습니다. "
                "Inspection/manus_agent.py가 adapter.py와 같은 폴더에 있는지 확인하세요."
            )
        self.timeout = timeout
        self.user_data_dir = user_data_dir
        self.screenshot_dir = screenshot_dir
        self._inner = None

    def __enter__(self):
        import os
        if not os.environ.get("DISPLAY"):
            raise RuntimeError(
                "Manus는 headed 실행이 필요합니다(헤드리스 차단). DISPLAY가 없습니다. "
                "run_fleet_manus.sh로 실행하거나 Xvfb(:99) 후 DISPLAY=:99를 설정하세요."
            )
        self._inner = ManusAgentAdapter(
            user_data_dir=self.user_data_dir, screenshot_dir=self.screenshot_dir,
            headless=False, timeout_s=int(self.timeout))
        self._inner.__enter__()
        return self

    def __exit__(self, *exc):
        if self._inner:
            return self._inner.__exit__(*exc)
        return False

    def reset(self) -> None:
        if self._inner and hasattr(self._inner, "reset"):
            self._inner.reset()

    def send(self, message: str) -> RawObservation:
        obs = self._inner.send(message)
        return RawObservation(
            visible_text=getattr(obs, "visible_text", ""),
            disclosed_steps=[],
            disclosure_format="opaque_browser_ui",
            observation_tier="T0",
            raw_panels=getattr(obs, "raw_panels", []),
            side_channels=getattr(obs, "side_channels", {}),
        )


# ─────────────────────────────────────────────────────────────
# Factory
# ─────────────────────────────────────────────────────────────
def make_adapter(
    url: str,
    headless: bool = True,
    model: str = "gemini-2.5-flash",
    proto: str = "auto",
) -> AgentAdapter:
    """
    proto 명시 또는 url로 어댑터 선택.

    proto:
      - auto
      - streamlit
      - api
      - mcp
      - a2a
      - goover
      - genspark
      - manus
    """
    proto = (proto or "auto").lower()

    if proto == "manus":
        return ManusAdapter(url, headless=headless)

    if proto == "genspark":
        return GensparkAdapter(url, headless=headless)

    if proto == "goover":
        return GooverAdapter(url, headless=headless)

    if proto == "mcp":
        return MCPAdapter(url, headless=headless)

    if proto == "a2a":
        return A2AAdapter(url, headless=headless)

    if proto == "api":
        return APIAdapter(url, model=model, headless=headless)

    if proto == "streamlit":
        return StreamlitAdapter(url, headless=headless)

    if "manus.im" in url:
        return ManusAdapter(url, headless=headless)

    if "genspark.ai" in url:
        return GensparkAdapter(url, headless=headless)

    if "goover.ai" in url:
        return GooverAdapter(url, headless=headless)

    if "/chat/completions" in url or "/v1/" in url:
        return APIAdapter(url, model=model, headless=headless)

    return StreamlitAdapter(url, headless=headless)


# ─────────────────────────────────────────────────────────────
# CLI smoke test
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://localhost:5501")
    ap.add_argument("--message", default="What are my recent transactions?")
    ap.add_argument("--proto", default="auto")
    ap.add_argument("--model", default="gemini-2.5-flash")
    ap.add_argument("--headed", action="store_true")
    args = ap.parse_args()

    with make_adapter(
        args.url,
        headless=not args.headed,
        model=args.model,
        proto=args.proto,
    ) as ad:
        obs = ad.send(args.message)

    print(
        json.dumps(
            {
                "tier": obs.observation_tier,
                "format": obs.disclosure_format,
                "disclosed_steps": obs.disclosed_steps,
                "visible_text_head": obs.visible_text[:700],
                "side_channels_keys": list(obs.side_channels.keys()),
                "source_count": obs.side_channels.get("source_count"),
                "screenshot": obs.side_channels.get("screenshot"),
            },
            ensure_ascii=False,
            indent=2,
        )
    )