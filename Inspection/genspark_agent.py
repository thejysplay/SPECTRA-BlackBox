#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Genspark 슈퍼 에이전트 어댑터 (SPECTRA 블랙박스용).

프롬프트 전송 → 응답 안정화 대기 → 답변/출처/스크린샷/full body 저장.

⚠️ 반드시 headed(실제 렌더링)로 실행해야 한다. Genspark은 headless 브라우저의
슈퍼에이전트 실행을 차단한다("이 리소스에 접근할 권한이 없습니다"). 서버에선
Xvfb 가상화면에 headed로 띄운다 → genspark_run.sh 사용(DISPLAY=:99).

로그인 세션은 프로필 .spectra_sessions/genspark 재사용(noVNC로 1회 로그인).

실행:
    bash Inspection/genspark_run.sh --message "질문..." --out out.json --timeout 300
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

# 상대 프로필/스크린샷 경로는 레포 루트 기준으로 고정(파이프라인이 Inspection/ 에서 돌아도 일치)
_REPO_ROOT = Path(__file__).resolve().parent.parent


@dataclass
class RawObservation:
    visible_text: str
    disclosed_steps: list = field(default_factory=list)
    disclosure_format: str = "opaque_browser_ui"
    observation_tier: str = "T0"
    raw_panels: list = field(default_factory=list)
    side_channels: dict = field(default_factory=dict)


class GensparkDenied(RuntimeError):
    """슈퍼에이전트 접근 거부(headless 차단 또는 계정 권한)."""


class GensparkAgentAdapter:
    HOME = "https://www.genspark.ai/"

    def __init__(
        self,
        user_data_dir: str = ".spectra_sessions/genspark",
        screenshot_dir: str = "genspark_shots",
        headless: bool = False,          # 반드시 headed (Xvfb)
        timeout_s: int = 300,
    ):
        _udd = Path(user_data_dir)
        _sd = Path(screenshot_dir)
        self.user_data_dir = _udd if _udd.is_absolute() else _REPO_ROOT / _udd
        self.screenshot_dir = _sd if _sd.is_absolute() else _REPO_ROOT / _sd
        self.headless = headless
        self.timeout_s = timeout_s
        self._pw = self._ctx = self.page = None

    # ── lifecycle ──────────────────────────────
    def __enter__(self):
        if not self.user_data_dir.exists():
            raise FileNotFoundError(
                f"로그인 프로필이 없습니다: {self.user_data_dir}\n"
                "먼저 noVNC 로그인: bash Inspection/novnc_up.sh "
                "https://www.genspark.ai/ .spectra_sessions/genspark"
            )
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)
        self._pw = sync_playwright().start()
        self._ctx = self._pw.chromium.launch_persistent_context(
            user_data_dir=str(self.user_data_dir),
            headless=self.headless,
            no_viewport=True,
            locale="ko-KR",
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--start-maximized",
                "--window-size=1440,1000",
                "--disable-blink-features=AutomationControlled",  # webdriver 숨김(headless 차단 회피 핵심)
            ],
        )
        self.page = self._ctx.pages[0] if self._ctx.pages else self._ctx.new_page()
        self.page.goto(self.HOME, wait_until="domcontentloaded", timeout=60_000)
        self._safe_networkidle()
        self.page.wait_for_timeout(2500)
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
        """
        시퀀스 사이 초기화 — 홈으로 돌아가 다음 send가 '새 대화'로 시작되게 한다.
        (시퀀스 내부 멀티턴은 reset 없이 같은 대화에 누적됨)
        로그인 세션은 persistent 프로필에 유지된다.
        """
        try:
            self.page.goto(self.HOME, wait_until="domcontentloaded", timeout=60_000)
            self._safe_networkidle(timeout=12_000)
            self.page.wait_for_timeout(1500)
        except Exception:
            pass

    # ── 입력창 ─────────────────────────────────
    def _find_input(self):
        sels = ['textarea', '[contenteditable="true"]', '[role="textbox"]',
                '[placeholder*="무엇" i]', '[placeholder*="물어" i]',
                '[placeholder*="입력" i]', 'input[type="text"]']
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

    # ── 상태 판별 ──────────────────────────────
    def _body_text(self) -> str:
        try:
            return self.page.locator("body").inner_text(timeout=5000)
        except Exception:
            return ""

    def _answer_text(self) -> str:
        """가장 최근 assistant 답변(.markdown-viewer 마지막 요소)."""
        loc = self.page.locator(".markdown-viewer")
        n = loc.count()
        if n == 0:
            return ""
        try:
            return (loc.nth(n - 1).inner_text(timeout=2000) or "").strip()
        except Exception:
            return ""

    def _is_generating(self) -> bool:
        body = self._body_text()
        return bool(re.search(
            r"(생성 중|생성하고|작업 중|검색 중|분석 중|조사 중|생각 중|"
            r"thinking|researching|generating|searching|working)",
            body, re.I))

    def _wait_for_answer(self, timeout_s: int) -> str:
        deadline = time.monotonic() + timeout_s
        last, stable, appeared = "", 0, False
        while time.monotonic() < deadline:
            body = self._body_text()
            if "권한이 없습니다" in body or "공유를 요청" in body:
                raise GensparkDenied(
                    "Genspark 접근 거부('권한이 없습니다'). headless로 실행했거나 "
                    "계정에 슈퍼에이전트 권한이 없을 수 있습니다. genspark_run.sh(headed)로 실행하세요."
                )
            ans = self._answer_text()
            gen = self._is_generating()
            if ans and len(ans) >= 2:
                appeared = True
            if appeared and ans == last:
                stable += 1
            else:
                stable, last = 0, ans
            # 완료: 답변 존재 + 생성중 아님 + 10초 안정
            if appeared and not gen and stable >= 5:
                return ans
            # 생성 표시가 있어도 24초 이상 안정이면 반환
            if appeared and stable >= 12:
                return ans
            self.page.wait_for_timeout(2000)
        return last  # timeout

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
                if re.search(r"genspark\.ai|accounts\.|login|signup", href, re.I):
                    continue
                txt = (a.inner_text(timeout=800) or "").strip()
                key = (href, txt)
                if key in seen:
                    continue
                seen.add(key)
                out.append({"text": txt[:200], "href": href})
        except Exception:
            pass
        return out

    def _screenshot(self, message: str) -> str:
        digest = hashlib.sha1(message.encode("utf-8")).hexdigest()[:10]
        ts = time.strftime("%Y%m%d_%H%M%S")
        p = self.screenshot_dir / f"genspark_{ts}_{digest}.png"
        self.page.screenshot(path=str(p), full_page=True)
        return str(p)

    # ── 표준 send ──────────────────────────────
    def send(self, message: str) -> RawObservation:
        before_url = self.page.url
        box = self._find_input()
        self._fill_and_submit(box, message)
        self.page.wait_for_timeout(2500)

        answer = self._wait_for_answer(self.timeout_s)
        self._safe_networkidle(timeout=8000)

        links = self._extract_links()
        screenshot = self._screenshot(message)

        return RawObservation(
            visible_text=answer,
            disclosure_format="opaque_browser_ui",
            observation_tier="T0",
            side_channels={
                "service": "genspark_super_agent",
                "prompt": message,
                "before_url": before_url,
                "after_url": self.page.url,
                "conversation_url": self.page.url,
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
    ap.add_argument("--out", default="genspark_observation.json")
    ap.add_argument("--user-data-dir", default=".spectra_sessions/genspark")
    ap.add_argument("--screenshot-dir", default="genspark_shots")
    ap.add_argument("--timeout", type=int, default=300, help="응답 대기 초(슈퍼에이전트 리서치는 길 수 있음)")
    ap.add_argument("--headless", action="store_true", help="(비권장) headless 강제 — 대개 차단됨")
    args = ap.parse_args()

    with GensparkAgentAdapter(
        user_data_dir=args.user_data_dir,
        screenshot_dir=args.screenshot_dir,
        headless=args.headless,
        timeout_s=args.timeout,
    ) as ad:
        obs = ad.send(args.message)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(asdict(obs), ensure_ascii=False, indent=2), encoding="utf-8")

    print("\n[OK] observation saved:", out_path)
    print("[conversation]", obs.side_channels.get("conversation_url"))
    print("[links]", obs.side_channels.get("link_count"))
    print("[screenshot]", obs.side_channels.get("screenshot"))
    print("\n--- answer ---")
    print(obs.visible_text[:2000])


if __name__ == "__main__":
    main()
