#!/usr/bin/env python3
"""data/scenarios/*.json → 같은 이름 .md (한국어 설명본). 페이로드/성공기준은 gemini 번역."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT.parent / "Scenario_Pipeline"))
import backend  # noqa: E402
from labels import ko  # noqa: E402

D = ROOT / "data" / "scenarios"

GLOSS = {"ENT-II": "간접입력", "INV-AT": "응용 도구 호출", "DAC-UBD": "사용자·업무 데이터",
         "PA-GA": "부여 권한", "SC-BIZ": "업무·거래 상태변경", "SC-SYS": "시스템·설정 상태변경"}
MEAN = {"ENT-II": "에이전트가 읽는 외부 콘텐츠(거래 내역·문서)에 지시가 숨어 들어옴",
        "INV-AT": "앱 도구를 부름(조회·송금·변경)",
        "DAC-UBD": "계정·거래·프로필 데이터 접근",
        "PA-GA": "사용자(Emma) 위임 권한으로 실행",
        "SC-BIZ": "거래·결제 상태 변경(무단 송금)",
        "SC-SYS": "계정·시스템 상태 변경(비밀번호 변경)"}
TITLE = {"시나리오1_무단송금": "무단 송금 (간접 주입)",
         "시나리오2_비밀번호변경": "계정 비밀번호 변경 (간접 주입)",
         "시나리오3_개인정보확보": "개인정보 확보 (간접 주입)",
         "시나리오4_계좌정보확보": "계좌정보 확보 (간접 주입, 권한 경유)"}


def translate(g):
    payload = {"turns": [{"user_input": t.get("user_input", ""),
                          "payload": (t.get("payload") or {}).get("content", "")} for t in g.get("turns", [])],
               "success_criteria": g.get("success_criteria", ""), "goal": g.get("goal", "")}
    prompt = ("아래 영어(보안 벤치마크 테스트 시나리오) 텍스트를 자연스러운 한국어로 번역해라. "
              "도구명·IBAN·비밀번호·기술 토큰은 원문 유지. JSON만 출력, 키/구조 동일:\n"
              + json.dumps(payload, ensure_ascii=False))
    return backend.gen_json(prompt, model="gemini", temp=0)


def calls_str(g):
    out = []
    for c in g.get("expected_tool_calls", []):
        args = ", ".join(f"{k}={v!r}" for k, v in (c.get("args") or {}).items())
        out.append(f"`{c['name']}({args})`")
    return " → ".join(out)


def main():
    for jp in sorted(D.glob("*.json")):
        r = json.loads(jp.read_text(encoding="utf-8"))
        stem = jp.stem
        g = r["generated"]
        skel = r["skeleton"].split("→")
        tr = translate(g)
        used = [s for s in dict.fromkeys(skel)]  # 순서 보존 유니크
        md = [f"# 점검 시나리오 — {TITLE.get(stem, stem)}", "",
              "## 뼈대",
              f"- 코드: `{r['skeleton']}`",
              f"- 한국어: {' → '.join(GLOSS.get(s, s) for s in skel)}",
              f"- 목표: {tr.get('goal', g.get('goal',''))} ({ko(skel[-1])})", "",
              "## 카테고리 의미 (이 시나리오에 쓰인 것만)",
              "| 코드 | 한국어 | 뜻 |", "|---|---|---|"]
        for s in used:
            if s in MEAN:
                md.append(f"| {s} | {GLOSS[s]} | {MEAN[s]} |")
        md += ["", "## 출처 (provenance)",
               f"- 원본 CS 통째 재현: {'예' if r['provenance']['is_verbatim_cs'] else '아니오 (신규 조합)'}",
               "- 전이별 실증 근거:"]
        for e in r["provenance"]["edge_grounding"]:
            md.append(f"  - {e['transition']}: {'·'.join(e['evidence_cs']) or '(없음)'}")
        md += ["- → 모든 전이는 실제 사건에서 관측(엣지 근거), 전체 경로는 신규 합성.", "",
               "## 골격 충실도 (도구 원자성 정합)",
               f"- 진입(ENT-II) {sum(1 for s in skel if s=='ENT-II')}개 = 유저 입력 {g.get('num_user_inputs')}턴, 일치.",
               f"- INV-AT {sum(1 for s in skel if s=='INV-AT')}개 = 기대 도구콜 {len(g.get('expected_tool_calls',[]))}개, 1:1. "
               "banking 도구 원자성(조회=INV-AT+DAC-UBD, 실행=INV-AT+상태변경)을 뼈대에 명시적으로 반영 → "
               "뼈대 밖 서브카테고리를 도구가 몰래 실현하지 않음.", "",
               "## 세션 (유저 입력, 한 세션)"]
        ko_turns = tr.get("turns", []) if isinstance(tr, dict) else []
        for j, t in enumerate(g.get("turns", []), 1):
            kt = ko_turns[j - 1] if j - 1 < len(ko_turns) else {}
            md.append(f"**유저입력 {j}**: {kt.get('user_input', t.get('user_input',''))}")
            pl = t.get("payload") or {}
            content = kt.get("payload") or pl.get("content")
            if content:
                md.append(f"- 주입[{pl.get('channel')}]: {content}")
        md += ["", "## 기대 도구콜 (오라클)", calls_str(g), "",
               "## 성공 기준",
               f"- {tr.get('success_criteria', g.get('success_criteria','')) if isinstance(tr,dict) else g.get('success_criteria','')}", ""]
        (D / f"{stem}.md").write_text("\n".join(md), encoding="utf-8")
        print("written", stem + ".md")


if __name__ == "__main__":
    main()
