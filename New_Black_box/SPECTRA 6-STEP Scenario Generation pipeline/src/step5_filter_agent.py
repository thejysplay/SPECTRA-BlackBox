#!/usr/bin/env python3
"""
STEP 5 (v7): 에이전트 필터 — 대상 에이전트가 지원하는 서브카테고리만 통과

STEP 4의 에이전트-무관 지식(1,531)에서, 특정 에이전트(여기선 AgentDojo banking)가
'실제로 할 수 있는' 서브카테고리만 남긴다. 한 시나리오의 모든 서브카테고리가
지원 집합에 있어야 통과.

banking 도구 → v7 서브카테고리 매핑은 아래 표에 명시(감사·조정 가능).
"""
import json
from pathlib import Path

from labels import ko, path_str

ROOT = Path(__file__).resolve().parent.parent
IN = ROOT / "data" / "step4_scenarios.json"
OUT = ROOT / "data" / "step5_banking.json"
OUT_MD = ROOT / "data" / "step5_banking.md"

AGENT = "AgentDojo_banking"

# banking 11개 도구 → 실현하는 v7 서브카테고리 (명시 매핑)
BANKING_TOOL_SUBCATS = {
    # 조회(READ): 도구 호출(INV-AT) + 데이터 접근(DAC)
    "get_iban":                     ["INV-AT", "DAC-UBD"],
    "get_balance":                  ["INV-AT", "DAC-UBD"],
    "get_most_recent_transactions": ["INV-AT", "DAC-UBD"],   # 거래 subject = 간접입력 반입구
    "get_scheduled_transactions":   ["INV-AT", "DAC-UBD"],
    "get_user_info":                ["INV-AT", "DAC-UBD"],
    # read_file이 읽는 실제 파일 = 청구서·집주인통지·주소변경 (업무 문서, 주입벡터 포함).
    # 시스템파일/자격증명 아님 → 파일·스토리지 도구(INV-AT) + 업무데이터(DAC-UBD).
    "read_file":                    ["INV-AT", "DAC-UBD"],
    # 실행(WRITE): 도구 호출 + 상태변경
    "send_money":                   ["INV-AT", "SC-BIZ"],    # 금융 도구 → 거래 상태
    "schedule_transaction":         ["INV-AT", "SC-BIZ"],
    "update_scheduled_transaction": ["INV-AT", "SC-BIZ"],
    "update_password":              ["INV-AT", "SC-SYS"],    # 계정 상태
    "update_user_info":             ["INV-AT", "SC-SYS"],
}
# 도구가 아니어도 에이전트가 본질적으로 가진 능력
ALWAYS = ["ENT-DI",   # 사용자 직접 입력
          "ENT-II",   # 간접입력(read_file 내용·거래 subject에 주입)
          "ID-RG"]    # 응답(결과) 생성

SUPPORTED = set(ALWAYS) | {s for subs in BANKING_TOOL_SUBCATS.values() for s in subs}

# 권한 컨텍스트 — 도구가 아니라 '운영 권한'이라 별도로 인정. 실행으로 발현 확인.
#   PA-GA: 에이전트가 사용자(Emma) 위임 권한으로 동작(시스템 프롬프트가 근거). 데이터가 아니라 권한(E3).
# 데이터 접근(DAC-CS 자격증명 / DAC-SRD 시스템런타임)은 '권한'이 아니라 데이터(E4)라,
# 기준은 "그 데이터를 반환하는 도구가 있는가"임. banking엔 없음(get_user_info는 password 제외,
# read_file은 업무문서만) → 다른 미도달 데이터와 동일하게 제거.
# (PA-CT·PA-ACB는 26 CS 미등장 → 어떤 시나리오에도 안 나오므로 대상 아님)
CONTEXT_TESTABLE = {"PA-GA"}
EFFECTIVE = SUPPORTED | CONTEXT_TESTABLE

# ── 도구 원자성 realizability (Decision A: STEP6 입력은 (a) 26개, realizable은 flag로만) ──
# banking엔 '순수 INV-AT' 도구가 없다. 데이터 접근(DAC-UBD)·상태변경(SC)은 반드시
# 도구 호출(INV-AT) 뒤에만 발생 가능. 첫 INV-AT 이전에 DAC-UBD/SC가 나오면 = 도구 없이 효과
# → 실현 불가. (ID-RG 종점·DAC-UBD 없는 상태변경은 realizable로 두고 STEP6 생성에서 처리.)
def is_realizable(skel):
    first_inv = skel.index("INV-AT") if "INV-AT" in skel else 10 ** 9
    for i, s in enumerate(skel):
        if s in ("DAC-UBD", "SC-BIZ", "SC-SYS") and i < first_inv:
            return False
    return True


def main():
    d = json.loads(IN.read_text(encoding="utf-8"))
    scen = [tuple(p.split("→")) for p in d["scenarios"]]

    # (a) 서브카테고리 지원(집합) 필터
    passed = [p for p in scen if set(p) <= EFFECTIVE]
    # 권한 컨텍스트(PA-GA)에 의존 → 실행으로 확인 필요
    testable = [p for p in passed if set(p) & CONTEXT_TESTABLE]
    confirmed = [p for p in passed if not (set(p) & CONTEXT_TESTABLE)]

    # (b) 도구 원자성 realizable 분류 (제거 아님 — Decision A: flag로만)
    realizable = [p for p in passed if is_realizable(p)]
    real_testable = [p for p in realizable if set(p) & CONTEXT_TESTABLE]
    real_confirmed = [p for p in realizable if not (set(p) & CONTEXT_TESTABLE)]
    unrealizable = [p for p in passed if not is_realizable(p)]

    from collections import Counter
    blockers = Counter()
    for p in scen:
        for s in set(p) - EFFECTIVE:
            blockers[s] += 1

    print(f"대상: {AGENT}")
    print(f"도구 실현 서브카테고리 {len(SUPPORTED)}: {', '.join(sorted(SUPPORTED))}")
    print(f"권한 컨텍스트(위임권한) {len(CONTEXT_TESTABLE)}: {', '.join(sorted(CONTEXT_TESTABLE))}")
    print(f"\nSTEP4 입력 {len(scen)} → (a) STEP5 통과(서브카테고리 지원): {len(passed)}")
    print(f"     ├ 도구로 바로 확정(PA-GA 없음): {len(confirmed)}")
    print(f"     └ 권한 컨텍스트 의존(PA-GA, 실행확인): {len(testable)}")
    print(f"  (b) 도구 원자성 realizable: {len(realizable)}  (실현불가 {len(unrealizable)} 제거)")
    print(f"     ├ 도구확정: {len(real_confirmed)}")
    print(f"     └ 실행확인: {len(real_testable)}")
    print(f"  ※ Decision A: STEP6 입력 = (a) {len(passed)}개, realizable은 각 뼈대 flag로만 실음")
    print("\n제거 유발 미지원 서브카테고리(메커니즘 부재) 상위:")
    for s, c in blockers.most_common(8):
        print(f"   {s}({ko(s)}): {c}")

    print("\n통과 시나리오 예시 5개:")
    for i, p in enumerate(sorted(passed, key=lambda p: (len(p), p))[:5], 1):
        flag = " [실행확인]" if set(p) & CONTEXT_TESTABLE else ""
        print(f"  {i}. {path_str(p)}{flag}")

    # Decision A: STEP6 입력 = (a) 지원분 26개. realizable은 각 뼈대 메타 flag.
    supported_sorted = sorted(passed, key=lambda p: (len(p), p))
    scenarios_supported = [{"skeleton": "→".join(p),
                            "realizable": is_realizable(p),
                            "context_testable": bool(set(p) & CONTEXT_TESTABLE)}
                           for p in supported_sorted]
    payload = {"agent": AGENT,
               "tool_realized": sorted(SUPPORTED),
               "context_testable": sorted(CONTEXT_TESTABLE),
               "tool_map": BANKING_TOOL_SUBCATS, "always": ALWAYS,
               "input_count": len(scen), "passed_count": len(passed),
               "confirmed_count": len(confirmed), "testable_count": len(testable),
               "realizable_count": len(realizable),
               "real_confirmed_count": len(real_confirmed), "real_testable_count": len(real_testable),
               "unrealizable_count": len(unrealizable),
               "blockers": dict(blockers.most_common()),
               # (a) 지원 26 = STEP6 입력(Decision A). 각 뼈대에 realizable flag.
               "scenarios_supported": scenarios_supported,
               "scenarios": ["→".join(p) for p in sorted(passed)],            # 지원 26 (하위호환)
               "scenarios_realizable": ["→".join(p) for p in sorted(realizable)],  # realizable 19 (참고)
               "scenarios_testable": ["→".join(p) for p in sorted(testable)]}
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")

    md = [f"# STEP 5 — 에이전트 필터: {AGENT}", "",
          f"STEP4 지식 {len(scen)} → STEP5 통과(서브카테고리 지원) **{len(passed)}** "
          f"· 도구확정 {len(confirmed)} + 권한컨텍스트 실행확인 {len(testable)}.", "",
          "## banking 도구 → 서브카테고리 (실현)", "",
          "| banking 도구 | 실현 서브카테고리 |", "|---|---|"]
    for t, subs in BANKING_TOOL_SUBCATS.items():
        md.append(f"| {t} | {', '.join(f'{s}({ko(s)})' for s in subs)} |")
    md += ["", f"+ 본질 능력: {', '.join(f'{s}({ko(s)})' for s in ALWAYS)}",
           "",
           "## 권한 컨텍스트 (도구 아님, 위임권한 → 실행으로 확인)",
           f"- PA-GA(부여 권한): 에이전트가 사용자 위임 권한으로 동작 (시스템 프롬프트 근거)",
           "",
           f"**도구 실현 집합({len(SUPPORTED)})**: {', '.join(sorted(SUPPORTED))}",
           f"**+ 테스트대상({len(CONTEXT_TESTABLE)})**: {', '.join(sorted(CONTEXT_TESTABLE))}",
           f"**메커니즘 부재로 제거**: EXE-*(실행)·PST-*(지속)·ID-ER(외부유출)·INT-*(편입)·HD-*·SC-DAT 등", "",
           "## 통과 시나리오 예시 (⚑=실행확인 필요)", ""]
    for i, p in enumerate(sorted(passed, key=lambda p: (len(p), p))[:12], 1):
        flag = " ⚑" if set(p) & CONTEXT_TESTABLE else ""
        md.append(f"{i}. {path_str(p)}{flag}")
    OUT_MD.write_text("\n".join(md), encoding="utf-8")
    print(f"\n  → {OUT.relative_to(ROOT)} · {OUT_MD.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
