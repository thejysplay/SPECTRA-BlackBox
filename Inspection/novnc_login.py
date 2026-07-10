#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
범용 noVNC 로그인 브라우저 — 서버 Xvfb 화면에 실제 크롬을 띄우고 유지한다.
사람은 noVNC(웹)로 이 화면을 보며 직접 로그인한다. 세션은 persistent 프로필에
지속 기록되므로, 로그인 후 이 프로세스를 내리면 프로필에 세션이 남는다.

전제: DISPLAY 가 Xvfb(:99 등)를 가리켜야 함(novnc_up.sh가 설정).
사용: DISPLAY=:99 python Inspection/novnc_login.py --url <URL> --profile <프로필경로>
"""
from __future__ import annotations

import argparse
import time
from pathlib import Path

from playwright.sync_api import sync_playwright


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True)
    ap.add_argument("--profile", required=True)
    ap.add_argument("--max-min", type=int, default=40, help="브라우저 유지 최대 분")
    args = ap.parse_args()

    Path(args.profile).mkdir(parents=True, exist_ok=True)
    with sync_playwright() as pw:
        ctx = pw.chromium.launch_persistent_context(
            user_data_dir=args.profile,
            headless=False,
            no_viewport=True,
            locale="ko-KR",
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--start-maximized",
                "--window-size=1440,900",
                "--window-position=0,0",
                "--disable-blink-features=AutomationControlled",
            ],
        )
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.goto(args.url, wait_until="domcontentloaded", timeout=60_000)
        print(f"[novnc] READY: {args.url} 로드됨. noVNC 화면에서 로그인하세요.", flush=True)
        print(f"[novnc] 프로필: {args.profile} (로그인 후 이 스택을 내리면 세션 보존)", flush=True)

        deadline = time.monotonic() + args.max_min * 60
        while time.monotonic() < deadline:
            page.wait_for_timeout(5000)   # 브라우저 유지(세션은 프로필에 지속 기록됨)
        print("[novnc] DONE: 유지 시간 종료.", flush=True)
        ctx.close()


if __name__ == "__main__":
    main()
