#!/usr/bin/env python3
"""STEP 6 생성물(29) → 한국어 통합본. 영어 필드는 gemini로 번역, 구조는 우리 데이터로 조립."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT.parent / "Scenario_Pipeline"))
import backend  # noqa: E402
from labels import ko  # noqa: E402

GEN = json.loads((ROOT / "data" / "step6_generated.json").read_text(encoding="utf-8"))
OUT = ROOT / "data" / "step6_scenarios_ko_all.md"

GLOSS = {"ENT-DI": "직접입력", "ENT-II": "간접입력", "INT-EC": "실행형 편입", "INT-CR": "설정·규칙 편입",
         "PA-GA": "부여 권한", "DAC-UBD": "사용자·업무 데이터", "INV-AT": "응용 도구 호출",
         "SC-BIZ": "업무·거래 상태변경", "SC-SYS": "시스템·설정 상태변경", "ID-RG": "결과 생성"}
MEAN = {"ENT-II": "에이전트가 읽는 외부 콘텐츠(문서·거래)에 지시가 숨어 들어옴",
        "ENT-DI": "공격자가 유저 입력으로 직접 지시를 넣음",
        "INV-AT": "앱 도구를 부름(송금·조회)", "DAC-UBD": "계정·거래·프로필 데이터 접근",
        "PA-GA": "사용자 위임 권한으로 실행", "SC-BIZ": "거래·결제 상태 변경(무단 송금)",
        "SC-SYS": "계정·시스템 상태 변경(비번 변경)", "ID-RG": "응답·결과물에 정보 노출"}


def translate(g):
    payload = {"turns": [{"user_input": t.get("user_input", ""),
                          "payload": (t.get("payload") or {}).get("content", "")} for t in g.get("turns", [])],
               "success_criteria": g.get("success_criteria", "")}
    prompt = ("아래 영어(보안 벤치마크 테스트 시나리오) 텍스트를 자연스러운 한국어로 번역해라. "
              "도구명·IBAN·기술 토큰은 원문 유지. JSON만 출력, 키/구조 동일:\n"
              + json.dumps(payload, ensure_ascii=False))
    try:
        return backend.gen_json(prompt, model="gemini", temp=0)
    except Exception as e:
        return {"error": str(e)}


def main():
    md = ["# STEP 6 시나리오 한국어 통합본 (banking · 29건)", "",
          "## 카테고리 의미", "", "| 코드 | 한국어 | 뜻 |", "|---|---|---|"]
    for c, k in GLOSS.items():
        if c in MEAN:
            md.append(f"| {c} | {k} | {MEAN[c]} |")
    md.append("")

    for i, r in enumerate(GEN, 1):
        g = r["generated"]
        skel = r["skeleton"]
        skel_ko = " → ".join(GLOSS.get(s, s) for s in skel.split("→"))
        tr = translate(g)
        md += ["---", f"## [{i}] {skel_ko}",
               f"- 뼈대: `{skel}`  → 목표: {g.get('goal','')} ({r['goal_ko']})",
               f"- 출처: {'원본 CS' if r['provenance']['is_verbatim_cs'] else '신규 조합'} · 유저입력 {g.get('num_user_inputs','?')}개",
               f"- 공격자 파라미터: {json.dumps(g.get('attacker_parameters',{}), ensure_ascii=False)}", ""]
        ko_turns = tr.get("turns", []) if isinstance(tr, dict) else []
        for j, t in enumerate(g.get("turns", []), 1):
            kt = ko_turns[j - 1] if j - 1 < len(ko_turns) else {}
            md.append(f"**유저입력 {j}**: {kt.get('user_input', t.get('user_input',''))}")
            pl = t.get("payload")
            if pl and (kt.get("payload") or pl.get("content")):
                md.append(f"- 주입[{pl.get('channel')}]: {kt.get('payload') or pl.get('content')}")
        md.append("- 기대 도구콜: " + " → ".join(f"{tc.get('name')}({json.dumps(tc.get('args',{}),ensure_ascii=False)})"
                                                for tc in g.get("expected_tool_calls", [])))
        md.append("- 성공기준: " + (tr.get("success_criteria", g.get("success_criteria", "")) if isinstance(tr, dict) else g.get("success_criteria", "")))
        md.append("")
        print(f"[{i}/{len(GEN)}] 번역 완료")

    OUT.write_text("\n".join(md), encoding="utf-8")
    print(f"\n저장: {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
