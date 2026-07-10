#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Goover BlackBox UI smoke adapter for SPECTRA.

목적:
- Goover 웹에 접속
- 질문 입력
- 응답 안정화 대기
- Goover 화면 노이즈 제거
- 최종 응답 후보, 링크, 스크린샷, full body text 저장
- RawObservation 유사 JSON 저장

설치:
  pip install playwright
  python -m playwright install chromium

실행:
  python Inspection/goover_smoke.py \
    --message "Goover가 무엇인지 3문장으로 설명해줘. 다른 뉴스나 추천 콘텐츠는 제외해줘." \
    --out goover_test.json \
    --timeout 240

브라우저 보면서 실행:
  python Inspection/goover_smoke.py \
    --headed \
    --login-wait 120 \
    --message "테스트야. Goover가 어떤 서비스인지 짧게 설명해줘." \
    --out goover_test.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright


@dataclass
class RawObservation:
    visible_text: str
    disclosed_steps: list = field(default_factory=list)
    disclosure_format: str = "opaque_browser_ui"
    observation_tier: str = "T0"
    raw_panels: list = field(default_factory=list)
    side_channels: dict = field(default_factory=dict)


class GooverSmokeAdapter:
    def __init__(
        self,
        url: str = "https://goover.ai/",
        headless: bool = True,
        user_data_dir: str = ".spectra_sessions/goover",
        screenshot_dir: str = "goover_shots",
        timeout_ms: int = 240_000,
    ):
        self.url = url
        self.headless = headless
        self.user_data_dir = Path(user_data_dir)
        self.screenshot_dir = Path(screenshot_dir)
        self.timeout_ms = timeout_ms

        self._sent_messages = []          # reset 이후 보낸 발화(멀티턴 에코 제거용)
        self._pw = None
        self._ctx = None
        self.page = None

    def __enter__(self):
        self.user_data_dir.mkdir(parents=True, exist_ok=True)
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)

        self._pw = sync_playwright().start()

        self._ctx = self._pw.chromium.launch_persistent_context(
            user_data_dir=str(self.user_data_dir),
            headless=self.headless,
            viewport={"width": 1440, "height": 1100},
            locale="ko-KR",
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ],
        )

        self.page = self._ctx.new_page()
        self.page.goto(self.url, wait_until="domcontentloaded", timeout=60_000)
        self._safe_wait_network_idle()
        return self

    def __exit__(self, *exc):
        try:
            if self._ctx:
                self._ctx.close()
        finally:
            if self._pw:
                self._pw.stop()
        return False

    def _safe_wait_network_idle(self, timeout: int = 15_000):
        try:
            self.page.wait_for_load_state("networkidle", timeout=timeout)
        except PlaywrightTimeoutError:
            pass

    def wait_for_manual_login(self, seconds: int):
        if seconds <= 0:
            return

        print(f"[login] {seconds}초 동안 브라우저에서 직접 로그인/초기화하세요.")
        print("[login] 로그인 완료 후에도 창을 닫지 마세요. 시간이 지나면 자동 진행합니다.")
        self.page.wait_for_timeout(seconds * 1000)


    def reset(self):
        """
        Goover는 답변 결과 화면에서 다음 입력창이 사라지거나 위치가 바뀔 수 있음.
        따라서 probe 사이에는 홈/검색 시작 화면으로 다시 이동한다.
        로그인 세션은 persistent context에 유지된다.
        """
        self._sent_messages = []          # 새 시나리오/프로브 시작 → 에코 대상 초기화
        self._goto_home()

    def _goto_home(self):
        """홈 화면으로 이동(UI 복구용). 세션 발화 누적(_sent_messages)은 건드리지 않는다.
        — 전송 중 입력창 재탐색 시 이걸 쓰면 멀티턴 에코 제거 대상이 유실되지 않는다."""
        try:
            self.page.goto(self.url, wait_until="domcontentloaded", timeout=60_000)
            self._safe_wait_network_idle(timeout=15_000)
            self.page.wait_for_timeout(2000)
        except Exception:
            pass

    # ─────────────────────────────────────────
    # 입력창 탐색
    # ─────────────────────────────────────────
    def _candidate_textboxes(self):
        selectors = [
            "textarea",
            '[contenteditable="true"]',
            '[role="textbox"]',
            'input[type="text"]',
            "input:not([type])",
            "div.ProseMirror",
            ".ProseMirror",
            '[data-testid*="input" i]',
            '[data-testid*="textarea" i]',
            '[placeholder*="Ask" i]',
            '[placeholder*="Search" i]',
            '[placeholder*="질문" i]',
            '[placeholder*="검색" i]',
            '[placeholder*="무엇" i]',
            '[placeholder*="메시지" i]',
        ]

        locators = []

        for sel in selectors:
            try:
                loc = self.page.locator(sel)
                count = loc.count()

                for i in range(min(count, 30)):
                    item = loc.nth(i)
                    if self._is_visible_and_enabled(item):
                        locators.append(item)

            except Exception:
                continue

        return locators

    def _is_visible_and_enabled(self, locator) -> bool:
        try:
            return locator.is_visible(timeout=800) and locator.is_enabled(timeout=800)
        except Exception:
            return False

    def _find_textbox(self):
        boxes = self._candidate_textboxes()

        # 결과 화면에서 입력창이 안 보이면 홈으로 돌아간 뒤 한 번 더 시도
        if not boxes:
            print("[input] textbox not found. reset to Goover home and retry...")
            self._goto_home()          # 홈 이동만 — _sent_messages(에코 대상) 보존
            boxes = self._candidate_textboxes()

        if not boxes:
            raise RuntimeError(
                "입력창을 자동으로 찾지 못했습니다. "
                "Goover UI가 바뀌었거나 로그인/온보딩 화면일 수 있습니다."
            )

        scored = []

        for box in boxes:
            try:
                bb = box.bounding_box()
                if not bb:
                    continue

                y = bb.get("y", 0)
                x = bb.get("x", 0)
                w = bb.get("width", 0)
                h = bb.get("height", 0)

                text = ""
                placeholder = ""
                aria = ""

                try:
                    text = (box.inner_text(timeout=500) or "").strip()
                except Exception:
                    pass

                try:
                    placeholder = box.get_attribute("placeholder") or ""
                except Exception:
                    pass

                try:
                    aria = box.get_attribute("aria-label") or ""
                except Exception:
                    pass

                label = " ".join([text, placeholder, aria])

                forbidden = re.compile(
                    r"(레퍼런스|지식 베이스|파일|URL|노트|수집 에이전트|그룹 에이전트|업로드|스크레이프)",
                    re.I,
                )

                if forbidden.search(label):
                    continue

                score = 0

                # 보통 메인 입력창은 화면 아래쪽 + 가로폭이 넓음
                score += y
                score += w * 0.3

                # 질문/검색 placeholder가 있으면 가산
                if re.search(r"(ask|search|질문|검색|무엇|메시지)", label, re.I):
                    score += 500

                # 너무 작은 검색 필드보다 큰 입력창 우선
                if w >= 400:
                    score += 300

                if h >= 30:
                    score += 50

                scored.append((score, y, x, box, label))

            except Exception:
                continue

        if not scored:
            # fallback
            return boxes[0]

        scored.sort(key=lambda x: x[0], reverse=True)

        best = scored[0]
        print(f"[input] selected textbox label={best[4]!r} y={best[1]} x={best[2]}")
        return best[3]

    # ─────────────────────────────────────────
    # 전송 버튼 탐색
    # ─────────────────────────────────────────
    def _candidate_send_buttons(self):
        """
        Goover에서 아무 button이나 누르면 '레퍼런스 추가' 같은 패널이 열릴 수 있음.
        따라서 명확히 전송/검색/질문 계열로 보이는 버튼만 후보로 잡는다.
        """
        selectors = [
            'button[aria-label*="send" i]',
            'button[aria-label*="submit" i]',
            'button[aria-label*="ask" i]',
            'button[aria-label*="search" i]',
            'button[aria-label*="검색" i]',
            'button[aria-label*="질문" i]',
            'button[aria-label*="전송" i]',
            'button[title*="send" i]',
            'button[title*="submit" i]',
            'button[title*="ask" i]',
            'button[title*="search" i]',
            'button[title*="검색" i]',
            'button[title*="질문" i]',
            'button[title*="전송" i]',
            'button:has-text("Send")',
            'button:has-text("Ask")',
            'button:has-text("Search")',
            'button:has-text("검색")',
            'button:has-text("질문")',
            'button:has-text("전송")',
            'button[type="submit"]',
        ]

        out = []

        for sel in selectors:
            try:
                loc = self.page.locator(sel)
                count = loc.count()

                for i in range(min(count, 20)):
                    item = loc.nth(i)

                    if self._is_visible_and_enabled(item):
                        out.append(item)

            except Exception:
                continue

        return out

    def _click_send_button_if_any(self) -> bool:
        """
        전송 버튼으로 확신되는 것만 클릭한다.
        '레퍼런스 추가', '파일', 'URL', '노트' 같은 버튼은 절대 클릭하지 않는다.
        """
        buttons = self._candidate_send_buttons()

        if not buttons:
            return False

        forbidden = re.compile(
            r"(레퍼런스|지식 베이스|파일|URL|노트|수집 에이전트|그룹 에이전트|업로드|스크레이프)",
            re.I,
        )

        positive = re.compile(
            r"(send|submit|ask|search|검색|질문|전송)",
            re.I,
        )

        scored = []

        for btn in buttons:
            try:
                text = ""
                aria = ""
                title = ""

                try:
                    text = (btn.inner_text(timeout=500) or "").strip()
                except Exception:
                    pass

                try:
                    aria = btn.get_attribute("aria-label") or ""
                except Exception:
                    pass

                try:
                    title = btn.get_attribute("title") or ""
                except Exception:
                    pass

                label = " ".join([text, aria, title]).strip()

                if forbidden.search(label):
                    continue

                # label이 있는 경우 positive만 허용
                if label and not positive.search(label):
                    continue

                bb = btn.bounding_box()
                if not bb:
                    continue

                y = bb.get("y", 0)
                x = bb.get("x", 0)
                w = bb.get("width", 0)
                h = bb.get("height", 0)

                score = y

                if positive.search(label):
                    score += 1000

                # 전송 버튼은 보통 입력창 오른쪽 아래 작은 버튼
                if 20 <= w <= 90 and 20 <= h <= 90:
                    score += 100

                scored.append((score, btn, label, y, x, w, h))

            except Exception:
                continue

        scored.sort(key=lambda x: x[0], reverse=True)

        for _, btn, label, y, x, w, h in scored:
            try:
                print(f"[send] click candidate: {label!r} y={y} x={x} w={w} h={h}")
                btn.click(timeout=1500)
                return True

            except Exception:
                continue

        return False

    # ─────────────────────────────────────────
    # 입력/전송
    # ─────────────────────────────────────────
    def _fill_textbox(self, box, message: str):
        box.click(timeout=5000)

        try:
            box.fill(message, timeout=3000)
            return

        except Exception:
            pass

        try:
            self.page.keyboard.press("Control+A")
            self.page.keyboard.press("Backspace")
            self.page.keyboard.type(message, delay=5)
            return

        except Exception as e:
            raise RuntimeError(f"입력 실패: {e}") from e

    def _send_message(self, message: str):
        """
        Goover에서는 버튼 클릭보다 Enter 전송을 먼저 시도한다.
        버튼 후보를 넓게 잡으면 '레퍼런스 추가' 같은 UI 버튼을 누를 위험이 큼.
        """
        box = self._find_textbox()
        self._fill_textbox(box, message)

        before = self._body_text()

        # 1순위: Enter 전송
        try:
            box.press("Enter")
            self.page.wait_for_timeout(2500)

            after = self._body_text()
            if after != before:
                print("[send] sent by Enter")
                return

        except Exception:
            pass

        # 2순위: Ctrl+Enter 전송
        try:
            box.press("Control+Enter")
            self.page.wait_for_timeout(2500)

            after = self._body_text()
            if after != before:
                print("[send] sent by Control+Enter")
                return

        except Exception:
            pass

        # 3순위: 명확히 전송 버튼으로 보이는 것만 클릭
        if self._click_send_button_if_any():
            self.page.wait_for_timeout(2500)
            print("[send] sent by button")
            return

        raise RuntimeError("질문 전송 실패: Enter/Ctrl+Enter/전송 버튼 모두 실패")

    # ─────────────────────────────────────────
    # 화면 텍스트/응답 대기
    # ─────────────────────────────────────────
    def _body_text(self) -> str:
        try:
            return self.page.locator("body").inner_text(timeout=5000)
        except Exception:
            return ""

    def _wait_for_response_stable(self, before_text: str, timeout_s: int = 240) -> str:
        """
        Goover는 질문 직후 '활동/참조/연관 콘텐츠'가 먼저 뜨고,
        최종 답변은 늦게 생성될 수 있음.

        따라서 단순 body 변화가 아니라:
        - Goover 진행 로그 제거 후 clean text를 만들고
        - clean text가 일정 시간 안정될 때까지 대기
        """
        deadline = time.monotonic() + timeout_s
        last_clean = ""
        stable = 0
        appeared = False

        while time.monotonic() < deadline:
            cur = self._body_text()
            clean = self._clean_goover_body(cur, before_text)

            loading_hint = bool(
                re.search(
                    r"(질문의 의도와 내용을 분석하고 있어요|검색하고 있어요|분석하고 있어요|"
                    r"답변을 생성|생성 중|검색 중|로딩|loading|searching|researching|generating)",
                    cur,
                    re.I,
                )
            )

            if clean and len(clean) >= 80:
                appeared = True

            if appeared and clean == last_clean:
                stable += 1
            else:
                stable = 0
                last_clean = clean

            # 로딩 문구가 없고 4초 안정
            if appeared and not loading_hint and stable >= 4:
                return cur

            # 로딩 문구가 있어도 clean 결과가 8초 안정이면 반환
            if appeared and stable >= 8:
                return cur

            self.page.wait_for_timeout(1000)

        # timeout이어도 현재 화면 반환
        return self._body_text()

    # ─────────────────────────────────────────
    # Goover 전용 본문 정제
    # ─────────────────────────────────────────
    def _clean_goover_body(self, text: str, before_text: str = "") -> str:
        """
        Goover body 전체에서 UI/활동/추천/출처 카드 노이즈를 제거하고
        실제 답변 본문만 최대한 남긴다.
        """
        t = text or ""

        # before_text와 공통 prefix 제거
        if before_text and t.startswith(before_text):
            t = t[len(before_text):]

        lines = [x.strip() for x in t.splitlines()]
        lines = [x for x in lines if x]

        noise_exact = {
            # 상단/좌측 메뉴
            "디스커버리",
            "브리핑 에이전트",
            "내 보관함",
            "게스트",
            "퀵 리서치",
            "선택 없음",
            "웹",
            "문서 기반 채팅",
            "GO OVER",
            "활동",
            "참조",
            "전체",
            "리포트",
            "토픽 서머리",
            "기업",
            "동영상",
            "소셜 미디어",

            # 레퍼런스 패널
            "레퍼런스 추가",
            "지식 베이스",
            "파일",
            "검색",
            "URL",
            "노트",
            "수집 에이전트",
            "그룹 에이전트",
            "전체 (0)",
            "파일 업로드 (0)",
            "스크레이프 모음 (0)",
            "검색 수집 (0)",
            "URL ・ RSS (0)",
            "클라우드 ・ 이메일 (0)",
            "블로그 ・ 소셜 (0)",
            "데이터 없음",
            "0개 문서 선택",

            # 진행 로그
            "질문의 의도와 내용을 분석하고 있어요.",
            "더 많은 인사이트 보기",
            "Goover가 찾은 연관 콘텐츠를 확인해보세요!",
        }

        # 이 문구가 나오면 실제 답변은 끝난 것으로 봄
        stop_markers = [
            "지금 바로 로그인하고",
            "이 답변이 부족하게 느껴지셨다면",
            "딥리서치를 통해",
            "딥 리서치",
            "Goover 플랫폼의",
            "AI 워크버디가",
            "Goover의 주요 사용 사례",
            "2026년 Goover",
            "활용 사례집",
            "Gen AI",
            "AI서비스 구버",
            "솔트룩스 AI 검색 엔진",
            "Smart Research with Goover",
            "GOOVER: 인공지능",
            "네이버와 GOOVER",
            "Goover AI:",
            "Medigatenews",
            "MEDI:GATE",
        ]

        cleaned = []

        for line in lines:
            if line in noise_exact:
                continue

            if any(m in line for m in stop_markers):
                break

            if re.search(
                r"(질문의 의도와 내용을 분석하고 있어요|검색하고 있어요|핵심 주제어|"
                r"선택 없음|문서 기반 채팅|레퍼런스|지식 베이스|파일 업로드|스크레이프|"
                r"더 많은 인사이트|연관 콘텐츠)",
                line,
            ):
                continue

            # 입력 에코 제거는 send()의 _strip_input_echo(message 기준)가 담당
            # (여기서 하드코딩 문구 매칭하던 로직 제거)

            # 너무 짧은 UI 조각 제거
            if len(line) <= 1:
                continue

            cleaned.append(line)

        result = "\n".join(cleaned).strip()

        # citation 번호 정리: 문장 끝의 " 1", " 4" 같은 단독 번호 제거
        result = re.sub(r"\s+\d+\s*$", "", result, flags=re.M)

        # 혹시 하단 카드가 남아 있으면 잘라냄
        hard_cut_patterns = [
            r"\n2026 SAC에서 공개된",
            r"\n활용 사례집",
            r"\nsaltlux",
            r"\nm blog naver",
            r"\nseo goover",
            r"\nMedigatenews",
            r"\nMEDI:GATE",
        ]

        for pat in hard_cut_patterns:
            m = re.search(pat, result)
            if m:
                result = result[:m.start()].strip()

        return result

    def _strip_input_echo(self, text: str, messages) -> str:
        """goover UI는 보낸 입력을 답변 앞에 (보통 2회) 그대로 에코한다.
        멀티턴에서는 이전 턴 발화까지 앞에 다시 나타나므로, 세션에서 보낸 '모든 발화'의
        줄과 일치하는 '선두' 줄을 제거해 실제 답변만 남긴다.
        선두 앵커 방식이라 답변이 우연히 질문 문구를 포함해도 잘리지 않는다."""
        if not text or not messages:
            return text
        if isinstance(messages, str):
            messages = [messages]
        norm = lambda s: re.sub(r"\s+", " ", s).strip()
        msg_lines = {norm(x) for m in messages for x in (m or "").splitlines() if norm(x)}
        if not msg_lines:
            return text
        lines = text.splitlines()
        i = 0
        while i < len(lines):
            ln = norm(lines[i])
            if not ln:
                i += 1
                continue
            is_echo = ln in msg_lines or (len(ln) >= 12 and any(ln in m or m in ln for m in msg_lines))
            if not is_echo:
                break
            i += 1
        return "\n".join(lines[i:]).strip()

    def _extract_visible_delta(self, before: str, after: str, messages=None) -> str:
        cleaned = self._clean_goover_body(after, before)
        if not cleaned and after.startswith(before):
            cleaned = after[len(before):].strip()
        if not cleaned:
            cleaned = after.strip()
        return self._strip_input_echo(cleaned, messages or [])

    # ─────────────────────────────────────────
    # 링크/스크린샷
    # ─────────────────────────────────────────
    def _extract_links(self) -> list[dict[str, str]]:
        links = []

        try:
            loc = self.page.locator("a[href]")
            count = loc.count()

        except Exception:
            return links

        seen = set()

        for i in range(min(count, 300)):
            try:
                a = loc.nth(i)
                href = a.get_attribute("href") or ""
                text = (a.inner_text(timeout=1000) or "").strip()

                if not href:
                    continue

                if href.startswith("javascript:") or href.startswith("#"):
                    continue

                key = (href, text)

                if key in seen:
                    continue

                seen.add(key)
                links.append(
                    {
                        "text": text[:300],
                        "href": href,
                    }
                )

            except Exception:
                continue

        return links

    def _source_like_links(self, links: list[dict[str, str]]) -> list[dict[str, str]]:
        out = []

        for x in links:
            href = x.get("href", "")

            if not href:
                continue

            # Goover 내부/로그인/계정 링크 제외
            if re.search(
                r"(goover\.ai|accounts\.google|login|signup|auth|logout|privacy|terms)",
                href,
                re.I,
            ):
                continue

            out.append(x)

        return out

    def _save_screenshot(self, message: str) -> str:
        digest = hashlib.sha1(message.encode("utf-8")).hexdigest()[:10]
        ts = time.strftime("%Y%m%d_%H%M%S")
        path = self.screenshot_dir / f"goover_{ts}_{digest}.png"

        self.page.screenshot(path=str(path), full_page=True)

        return str(path)

    # ─────────────────────────────────────────
    # 표준 send
    # ─────────────────────────────────────────
    def send(self, message: str) -> RawObservation:
        self._sent_messages.append(message)      # 멀티턴: 이전 턴 발화 에코까지 제거 대상에 포함
        msgs_snapshot = list(self._sent_messages)  # 전송 중 홈이동/초기화가 나도 에코 대상 보존
        before_text = self._body_text()
        before_url = self.page.url

        self._send_message(message)

        after_text = self._wait_for_response_stable(
            before_text=before_text,
            timeout_s=max(30, self.timeout_ms // 1000),
        )

        self._safe_wait_network_idle(timeout=10_000)

        links = self._extract_links()
        source_like_links = self._source_like_links(links)
        screenshot = self._save_screenshot(message)
        visible_text = self._extract_visible_delta(before_text, after_text, msgs_snapshot)

        obs = RawObservation(
            visible_text=visible_text,
            disclosed_steps=[],
            disclosure_format="opaque_browser_ui",
            observation_tier="T0",
            raw_panels=[],
            side_channels={
                "service": "goover",
                "before_url": before_url,
                "after_url": self.page.url,
                "title": self.page.title(),
                "all_links": links,
                "source_like_links": source_like_links,
                "source_count": len(source_like_links),
                "screenshot": screenshot,
                "full_body_text": after_text,
            },
        )

        return obs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="https://goover.ai/")
    ap.add_argument("--message", required=True)
    ap.add_argument("--headed", action="store_true", help="브라우저 창 보이게 실행")
    ap.add_argument("--login-wait", type=int, default=0, help="수동 로그인 대기 초")
    ap.add_argument("--user-data-dir", default=".spectra_sessions/goover")
    ap.add_argument("--screenshot-dir", default="goover_shots")
    ap.add_argument("--out", default="goover_observation.json")
    ap.add_argument("--timeout", type=int, default=240, help="응답 대기 초")
    args = ap.parse_args()

    with GooverSmokeAdapter(
        url=args.url,
        headless=not args.headed,
        user_data_dir=args.user_data_dir,
        screenshot_dir=args.screenshot_dir,
        timeout_ms=args.timeout * 1000,
    ) as ad:
        ad.wait_for_manual_login(args.login_wait)
        obs = ad.send(args.message)

    data = asdict(obs)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("\n[OK] observation saved:", out_path)
    print("[tier]", obs.observation_tier)
    print("[format]", obs.disclosure_format)
    print("[source_count]", obs.side_channels.get("source_count"))
    print("[screenshot]", obs.side_channels.get("screenshot"))
    print("\n--- visible_text head ---")
    print(obs.visible_text[:1200])


if __name__ == "__main__":
    main()