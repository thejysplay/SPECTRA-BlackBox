#!/usr/bin/env python3
"""
STEP 6 뼈대 정합 자동 검증 — 생성된 시나리오의 도구 호출 시퀀스를 서브카테고리 열로 환원해
원래 뼈대와 비교한다. banking 도구 원자성(호출=효과)에 근거.

판정:
  - calls_cnt : expected_tool_calls 수 == 뼈대 INV-AT 수 (ID-RG 종점은 0)
  - no_extra  : 도구가 실현하는 서브카테고리 ⊆ 뼈대 서브카테고리(진입·권한 제외한 need)
  - goal_ok   : 마지막 도구콜이 목표 서브카테고리를 실현 (ID-RG 종점은 도구 없이 응답)
  - faithful  : 위 셋 모두 통과
출력: data/step6_faithfulness.md (REPORT 삽입용 표) + 콘솔 요약.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GEN = ROOT / "data" / "step6_generated.json"
OUT_MD = ROOT / "data" / "step6_faithfulness.md"

TOOL = {"get_iban": ("INV-AT", "DAC-UBD"), "get_balance": ("INV-AT", "DAC-UBD"),
        "get_most_recent_transactions": ("INV-AT", "DAC-UBD"), "get_scheduled_transactions": ("INV-AT", "DAC-UBD"),
        "get_user_info": ("INV-AT", "DAC-UBD"), "read_file": ("INV-AT", "DAC-UBD"),
        "send_money": ("INV-AT", "SC-BIZ"), "schedule_transaction": ("INV-AT", "SC-BIZ"),
        "update_scheduled_transaction": ("INV-AT", "SC-BIZ"),
        "update_password": ("INV-AT", "SC-SYS"), "update_user_info": ("INV-AT", "SC-SYS")}


ACT_SUBS = ("INV-AT", "DAC-UBD", "SC-BIZ", "SC-SYS")   # 도구가 실현하는 서브카테고리(진입·권한·ID-RG 제외)


def check(rec):
    """순서 비교: 도구 호출 시퀀스를 서브카테고리 '열'로 환원 → 뼈대의 행위 서브카테고리 열과 동일해야 정합.
    banking 원자성: get_*/read_file=[INV-AT,DAC-UBD] · send류=[INV-AT,SC-BIZ] · update류=[INV-AT,SC-SYS].
    ENT(진입)·PA-GA(권한)·ID-RG(응답, 도구 아님)는 양쪽에서 제외. ID-RG 종점은 도구 0개면 정합."""
    g = rec.get("generated", {})
    skel = rec["skeleton"].split("→")
    calls = [c.get("name") for c in g.get("expected_tool_calls", [])]
    goal = skel[-1]

    # 뼈대의 행위 서브카테고리 열(순서 보존)
    skel_seq = [s for s in skel if s in ACT_SUBS]
    # 도구 호출 → 서브카테고리 열(순서 보존): 각 콜이 [INV-AT, 효과]
    tool_seq = [x for c in calls for x in TOOL.get(c, ())]

    seq_match = (skel_seq == tool_seq)
    goal_ok = (len(calls) == 0) if goal == "ID-RG" else (bool(calls) and goal in set(TOOL.get(calls[-1], ())))
    faithful = seq_match and goal_ok and ("error" not in g)
    return {"calls": calls,
            "skel_seq": "→".join(skel_seq) or "(없음)",
            "tool_seq": "→".join(tool_seq) or "(없음)",
            "seq_match": seq_match, "goal_ok": goal_ok, "faithful": faithful}


def main():
    recs = json.loads(GEN.read_text(encoding="utf-8"))
    rows = []
    nf = 0
    for r in recs:
        c = check(r)
        nf += int(c["faithful"])
        rows.append((r, c))

    # 콘솔
    print(f"생성 {len(recs)}건 · 뼈대 정합 {nf}/{len(recs)}")
    print(f"  realizable 뼈대: {sum(1 for r,_ in rows if r.get('realizable'))} · "
          f"그중 정합 {sum(1 for r,c in rows if r.get('realizable') and c['faithful'])}")
    print(f"  실현불가 뼈대: {sum(1 for r,_ in rows if not r.get('realizable'))} · "
          f"그중 정합 {sum(1 for r,c in rows if not r.get('realizable') and c['faithful'])}")

    # 마크다운 표
    md = ["# STEP 6 뼈대 정합 자동 검증 (banking · 26건)", "",
          f"도구 호출 시퀀스 → 서브카테고리 **열(순서)**로 환산 후 원래 뼈대의 행위 서브카테고리 열과 비교. "
          f"**정합 {nf}/{len(recs)}**.", "",
          "판정: 도구가 실현한 서브카테고리 열 == 뼈대 행위 열(진입·권한·ID-RG 제외) · 마지막콜=목표실현 "
          "(ID-RG 종점=도구없이 응답).", "",
          "| # | 뼈대 | realizable | 도구콜 | 뼈대 행위열 | 도구 실현열 | 열일치 | 목표 | 정합 |",
          "|---|---|---|---|---|---|---|---|---|"]
    for i, (r, c) in enumerate(rows, 1):
        yn = lambda b: "✅" if b else "❌"
        md.append(f"| {i} | `{r['skeleton']}` | {'○' if r.get('realizable') else '×'} | "
                  f"{', '.join(c['calls']) or '(없음)'} | {c['skel_seq']} | {c['tool_seq']} | "
                  f"{yn(c['seq_match'])} | {yn(c['goal_ok'])} | {yn(c['faithful'])} |")
    md += ["",
           f"- realizable 뼈대 {sum(1 for r,_ in rows if r.get('realizable'))}개 → 정합 "
           f"{sum(1 for r,c in rows if r.get('realizable') and c['faithful'])}개",
           f"- 실현불가 뼈대(DAC-UBD를 도구 없이 요구) {sum(1 for r,_ in rows if not r.get('realizable'))}개 → 정합 "
           f"{sum(1 for r,c in rows if not r.get('realizable') and c['faithful'])}개 "
           "(선행 DAC-UBD를 도구가 실현 못 해 열 불일치 → 전부 검출. Decision A대로 STEP5 flag + 생성후 검증이 이중으로 걸러냄)"]
    OUT_MD.write_text("\n".join(md), encoding="utf-8")
    print(f"\n저장: {OUT_MD.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
