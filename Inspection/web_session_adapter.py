#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
범용 로그인 세션 재사용 어댑터 — noVNC로 로그인한 프로필을 헤드리스로 재사용.

로그인은 novnc_up.sh 로 서버에서 1회 수행되고, 세션은 프로필 폴더에 남는다
(쿠키+localStorage+IndexedDB 포함 → storage_state JSON보다 완전).

제약: persistent context는 한 번에 하나의 프로세스만 프로필을 연다.
(noVNC 로그인 스택이 떠 있으면 novnc_down.sh 로 먼저 내릴 것.)

사용:
    VENV Inspection/web_session_adapter.py --profile .spectra_sessions/genspark --url https://www.genspark.ai/
"""
from __future__ import annotations

import argparse
import time
from pathlib import Path

from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout


class WebSessionAdapter:
    def __init__(self, profile: str, url: str, headless: bool = True,
                 shot_dir: str = "web_shots"):
        self.profile = Path(profile)
        self.url = url
        self.headless = headless
        self.shot_dir = Path(shot_dir)
        self._pw = self._ctx = self.page = None

    def __enter__(self):
        if not self.profile.exists():
            raise FileNotFoundError(
                f"로그인 프로필이 없습니다: {self.profile}\n"
                f"먼저 로그인: bash Inspection/novnc_up.sh {self.url} {self.profile}"
            )
        self.shot_dir.mkdir(parents=True, exist_ok=True)
        self._pw = sync_playwright().start()
        self._ctx = self._pw.chromium.launch_persistent_context(
            user_data_dir=str(self.profile),
            headless=self.headless,
            locale="ko-KR",
            viewport={"width": 1440, "height": 1100},
            args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu",
                  "--disable-blink-features=AutomationControlled"],
        )
        self.page = self._ctx.pages[0] if self._ctx.pages else self._ctx.new_page()
        self.page.goto(self.url, wait_until="domcontentloaded", timeout=60_000)
        try:
            self.page.wait_for_load_state("networkidle", timeout=15_000)
        except PWTimeout:
            pass
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

    def screenshot(self, tag: str = "session") -> str:
        ts = time.strftime("%Y%m%d_%H%M%S")
        p = self.shot_dir / f"{tag}_{ts}.png"
        self.page.screenshot(path=str(p), full_page=True)
        return str(p)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", required=True)
    ap.add_argument("--url", required=True)
    ap.add_argument("--headed", action="store_true")
    args = ap.parse_args()

    with WebSessionAdapter(profile=args.profile, url=args.url,
                           headless=not args.headed) as ad:
        print("[url]", ad.page.url)
        print("[title]", ad.page.title())
        print("[cookies]", len(ad._ctx.cookies()))
        print("[shot]", ad.screenshot("session_ready"))
        # ad.page 가 로그인된 상태로 준비됨 — 여기에 자동화 로직을 붙인다.


if __name__ == "__main__":
    main()
