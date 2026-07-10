#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Manus(마누스) 에이전트 어댑터 (SPECTRA 블랙박스용).

프롬프트 전송 → 작업(task) 완료 대기 → 답변/스크린샷/full body 저장.

⚠️ 반드시 headed(실제 렌더링). Manus는 로그인에 Cloudflare Turnstile/hCaptcha가
있고 자동화 브라우저를 차단하므로, 서버에선 Xvfb 가상화면에 headed로 띄운다
(manus_run.sh, DISPLAY=:99). 로그인 세션은 프로필 .spectra_sessions/manus 재사용.

Manus는 자율 에이전트라 작업이 길 수 있다(리서치·빌드는 수 분~수십 분).
완료 신호 = 화면에 "작업 완료" 표시 + 본문 안정.

실행:
    bash Inspection/manus_run.sh --message "프롬프트" --out out.json --timeout 600
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

from playwright.sync_api import sync_playwright
from playwright.sync_api import TimeoutError as PWTimeout

_REPO_ROOT = Path(__file__).resolve().parent.parent


@dataclass
class RawObservation:
    visible_text: str
    disclosed_steps: list = field(default_factory=list)
    disclosure_format: str = "opaque_browser_ui"
    observation_tier: str = "T0"
    raw_panels: list = field(default_factory=list)
    side_channels: dict = field(default_factory=dict)


# 답변 정제 시 제거할 UI 크롬/프로모 라인(정확 일치)
_NOISE_EXACT = {
    "Manus 1.6 Lite", "Manus 1.6", "Manus", "Lite", "업그레이드", "공유",
    "다운로드", "작업", "에이전트", "플러그인", "예약됨", "라이브러리",
    "프로젝트", "새 프로젝트", "모두 거부", "모두 수락", "사용자 정의",
}
# 이 문구가 나오면 답변 종료로 간주(이후는 프로모/추천칩)
_STOP_MARKERS = ["작업 완료", "무료 Manus", "체험판을 받으셨습니다", "업그레이드하세요"]


class ManusAgentAdapter:
    APP = "https://manus.im/app"

    def __init__(self, user_data_dir=".spectra_sessions/manus",
                 screenshot_dir="manus_shots", headless=False, timeout_s=600):
        _udd = Path(user_data_dir)
        _sd = Path(screenshot_dir)
        self.user_data_dir = _udd if _udd.is_absolute() else _REPO_ROOT / _udd
        self.screenshot_dir = _sd if _sd.is_absolute() else _REPO_ROOT / _sd
        self.headless = headless
        self.timeout_s = timeout_s
        self._pw = self._ctx = self.page = None
        self._last_prompt = ""

    # ── lifecycle ──────────────────────────────
    def __enter__(self):
        if not self.user_data_dir.exists():
            raise FileNotFoundError(
                f"로그인 프로필이 없습니다: {self.user_data_dir}\n"
                "먼저 noVNC 로그인: bash Inspection/novnc_up.sh "
                "https://manus.im/app .spectra_sessions/manus"
            )
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)
        self._pw = sync_playwright().start()
        self._ctx = self._pw.chromium.launch_persistent_context(
            user_data_dir=str(self.user_data_dir),
            headless=self.headless,
            no_viewport=True,
            locale="ko-KR",
            args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu",
                  "--start-maximized", "--window-size=1440,1000",
                  "--disable-blink-features=AutomationControlled"],
        )
        self.page = self._ctx.pages[0] if self._ctx.pages else self._ctx.new_page()
        self.page.goto(self.APP, wait_until="domcontentloaded", timeout=60_000)
        self._safe_networkidle()
        self.page.wait_for_timeout(2500)
        if "/login" in self.page.url:
            raise RuntimeError("Manus 로그인 세션 만료 — noVNC로 재로그인 필요(.spectra_sessions/manus).")
        return self

    def __exit__(self, *exc):
        try:
            if self._ctx:
                self._ctx.close()
        finally:
            if self._pw:
                self._pw.stop()
        return False

    def _safe_networkidle(self, timeout: int = 15_000):
        try:
            self.page.wait_for_load_state("networkidle", timeout=timeout)
        except PWTimeout:
            pass

    def reset(self) -> None:
        """새 작업으로 시작 — 홈(/app)으로 이동."""
        try:
            self.page.goto(self.APP, wait_until="domcontentloaded", timeout=60_000)
            self._safe_networkidle(timeout=12_000)
            self.page.wait_for_timeout(1800)
        except Exception:
            pass

    # ── 입력창 ─────────────────────────────────
    def _find_input(self):
        sels = ['textarea', '[contenteditable="true"]', '[role="textbox"]',
                '[placeholder*="무엇" i]', '[placeholder*="도와" i]', '[placeholder*="Ask" i]']
        best, best_w = None, -1
        for s in sels:
            loc = self.page.locator(s)
            for i in range(min(loc.count(), 12)):
                el = loc.nth(i)
                try:
                    if not el.is_visible(timeout=300):
                        continue
                    bb = el.bounding_box()
                    w = bb["width"] if bb else 0
                    if w > best_w:
                        best, best_w = el, w
                except Exception:
                    pass
        if not best:
            raise RuntimeError("입력창을 찾지 못했습니다 (UI 변경?).")
        return best

    def _fill_and_submit(self, box, message: str):
        box.click(timeout=5000)
        try:
            box.fill(message, timeout=3000)
        except Exception:
            self.page.keyboard.type(message, delay=8)
        self.page.wait_for_timeout(400)
        box.press("Enter")

    # ── 상태/응답 ──────────────────────────────
    def _body_text(self) -> str:
        try:
            return self.page.locator("body").inner_text(timeout=5000)
        except Exception:
            return ""

    def _msg_list_text(self) -> str:
        loc = self.page.locator('[class*="chat-message-list"]')
        if loc.count():
            try:
                return (loc.last.inner_text(timeout=3000) or "").strip()
            except Exception:
                pass
        return self._body_text()

    def _is_done(self) -> bool:
        return "작업 완료" in self._body_text()

    def _clean_answer(self, raw: str) -> str:
        lines = [x.strip() for x in (raw or "").splitlines()]
        lines = [x for x in lines if x]
        out = []
        for ln in lines:
            if any(m in ln for m in _STOP_MARKERS):   # 답변 종료 지점
                break
            if ln in _NOISE_EXACT:
                continue
            if self._last_prompt and ln == self._last_prompt.strip():   # 프롬프트 에코 제거
                continue
            if len(ln) <= 1 and not ln.isdigit():
                continue
            out.append(ln)
        return "\n".join(out).strip()

    def _wait_for_answer(self, timeout_s: int) -> str:
        deadline = time.monotonic() + timeout_s
        last_clean, stable, appeared = "", 0, False
        while time.monotonic() < deadline:
            done = self._is_done()
            clean = self._clean_answer(self._msg_list_text())
            if clean and len(clean) >= 1:
                appeared = True
            if appeared and clean == last_clean:
                stable += 1
            else:
                stable, last_clean = 0, clean
            # 완료 마커 뜨고 본문 안정
            if done and appeared and stable >= 2:
                return clean
            # 완료 마커 없어도 오래 안정이면 반환(마커 문구 변형 대비)
            if appeared and stable >= 15:
                return clean
            self.page.wait_for_timeout(3000)
        return last_clean

    # ── 링크/스크린샷 ──────────────────────────
    def _extract_links(self) -> list[dict]:
        out, seen = [], set()
        try:
            loc = self.page.locator("a[href]")
            for i in range(min(loc.count(), 200)):
                a = loc.nth(i)
                href = a.get_attribute("href") or ""
                if not href or href.startswith(("javascript:", "#")):
                    continue
                if re.search(r"manus\.im|accounts\.|login|signup|stripe", href, re.I):
                    continue
                txt = (a.inner_text(timeout=800) or "").strip()
                if (href, txt) in seen:
                    continue
                seen.add((href, txt))
                out.append({"text": txt[:200], "href": href})
        except Exception:
            pass
        return out

    def _screenshot(self, message: str) -> str:
        digest = hashlib.sha1(message.encode("utf-8")).hexdigest()[:10]
        ts = time.strftime("%Y%m%d_%H%M%S")
        p = self.screenshot_dir / f"manus_{ts}_{digest}.png"
        self.page.screenshot(path=str(p), full_page=True)
        return str(p)

    # ── 표준 send ──────────────────────────────
    def send(self, message: str) -> RawObservation:
        self._last_prompt = message
        before_url = self.page.url
        box = self._find_input()
        self._fill_and_submit(box, message)
        self.page.wait_for_timeout(3000)

        answer = self._wait_for_answer(self.timeout_s)
        self._safe_networkidle(timeout=8000)

        links = self._extract_links()
        screenshot = self._screenshot(message)
        return RawObservation(
            visible_text=answer,
            side_channels={
                "service": "manus",
                "prompt": message,
                "before_url": before_url,
                "after_url": self.page.url,
                "conversation_url": self.page.url,   # /app/<taskid>
                "title": self.page.title(),
                "links": links,
                "link_count": len(links),
                "screenshot": screenshot,
                "full_body_text": self._body_text(),
            },
        )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--message", required=True)
    ap.add_argument("--out", default="manus_observation.json")
    ap.add_argument("--user-data-dir", default=".spectra_sessions/manus")
    ap.add_argument("--screenshot-dir", default="manus_shots")
    ap.add_argument("--timeout", type=int, default=600, help="작업 완료 대기 초(에이전트 작업은 길다)")
    ap.add_argument("--headless", action="store_true", help="(비권장) 대개 차단됨")
    a = ap.parse_args()

    with ManusAgentAdapter(user_data_dir=a.user_data_dir, screenshot_dir=a.screenshot_dir,
                           headless=a.headless, timeout_s=a.timeout) as ad:
        obs = ad.send(a.message)

    out = Path(a.out); out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(asdict(obs), ensure_ascii=False, indent=2), encoding="utf-8")
    print("\n[OK] observation saved:", out)
    print("[conversation]", obs.side_channels.get("conversation_url"))
    print("[screenshot]", obs.side_channels.get("screenshot"))
    print("\n--- answer ---")
    print(obs.visible_text[:2000])


if __name__ == "__main__":
    main()
