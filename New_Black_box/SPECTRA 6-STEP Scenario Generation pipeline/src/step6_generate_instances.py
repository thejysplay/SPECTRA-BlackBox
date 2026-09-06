#!/usr/bin/env python3
"""
STEP 6 (v7): 인스턴스 조합 — 서브카테고리 시나리오 → 구체 인스턴스 시나리오

Decision A: STEP6 입력 = STEP5 (a) 서브카테고리 지원분 26개(원자성 필터 前). 각 뼈대를
banking이 realize하는 인스턴스로 펼친다. realizable 19는 참고치로 병기.
한 skeleton의 조합수 = 위치별 인스턴스 수의 곱 (반복 노드도 각 위치 독립 → 서로 다른 인스턴스 가능).
전량은 크므로 skeleton당 K개 샘플로 구체 시나리오 생성.
"""
import json
import random
from itertools import product
from pathlib import Path

from labels import ko, path_str

ROOT = Path(__file__).resolve().parent.parent
IN = ROOT / "data" / "step5_banking.json"
OUT = ROOT / "data" / "step6_banking_instances.json"
OUT_MD = ROOT / "data" / "step6_banking_instances.md"
K = 2   # skeleton당 샘플 인스턴스 조합 수

# banking이 각 서브카테고리에서 실제로 realize하는 인스턴스 (+ 실현 도구)
BANKING_INSTANCES = {
    "ENT-DI":  [("Chat / UI Input", "(사용자 입력)")],
    "ENT-II":  [("File / Document", "read_file"),
                ("Application / Service Record", "get_*_transactions(거래 subject)")],
    "INV-AT":  [("File / Storage Tool", "read_file"),
                ("Search / Retrieval Tool", "get_balance/iban/transactions"),
                ("Payment / Financial Tool", "send_money/schedule_transaction")],
    "DAC-UBD": [("Account / Payment Data", "get_balance/get_iban"),
                ("Transaction Data", "get_*_transactions"),
                ("Contact / Profile Data", "get_user_info"),
                ("Work Document", "read_file")],
    "SC-BIZ":  [("Transaction / Payment State", "send_money/schedule_transaction")],
    "SC-SYS":  [("User / Account State", "update_password/update_user_info")],
    "ID-RG":   [("Text / Response", "(에이전트 응답)")],
    "PA-GA":   [("User-delegated Authority", "(위임 권한 컨텍스트)")],
}


def combos_count(seq):
    """위치별 인스턴스 조합 수(반복 노드는 각 위치 독립 — 같은 노드도 다른 인스턴스 가능)."""
    n = 1
    for s in seq:                       # set(seq) 아님: 위치별로
        n *= len(BANKING_INSTANCES.get(s, [("?", "")]))
    return n


def instantiate(seq, k, rng):
    """seq를 인스턴스 열 k개로 샘플. 각 위치를 독립 선택(반복 노드도 서로 다른 인스턴스 가능)."""
    per_pos = [BANKING_INSTANCES.get(s, [("?", "")]) for s in seq]   # 위치별 후보
    full = list(product(*per_pos))
    rng.shuffle(full)
    out = []
    for choice in full[:k]:
        inst_seq = [(seq[i], choice[i][0], choice[i][1]) for i in range(len(seq))]
        out.append(inst_seq)
    return out


def main():
    d = json.loads(IN.read_text(encoding="utf-8"))
    scen = [tuple(p.split("→")) for p in d["scenarios"]]
    testable = {tuple(p.split("→")) for p in d.get("scenarios_testable", [])}

    total_full = sum(combos_count(s) for s in scen)
    rng = random.Random(7)
    generated = []
    for s in scen:
        for inst in instantiate(s, K, rng):
            generated.append({"skeleton": "→".join(s),
                              "testable": s in testable,
                              "instances": [{"sub": a, "instance": b, "tool": c} for a, b, c in inst]})

    real = [tuple(p.split("→")) for p in d.get("scenarios_realizable", [])]
    real_full = sum(combos_count(s) for s in real)
    print(f"입력 skeleton(Decision A, 지원 26): {len(scen)}개")
    print(f"전체 인스턴스 조합 공간(위치별): {total_full}")
    print(f"skeleton당 K={K} 샘플 → 구체 시나리오 {len(generated)}개")
    print(f"  (참고) realizable {len(real)}개: 위치별 조합 {real_full} · K={K} → {K*len(real)}")

    payload = {"agent": "AgentDojo_banking", "K": K,
               "n_skeletons": len(scen),
               "full_combination_space": total_full,
               "n_generated": len(generated),
               "realizable_n_skeletons": len(real),
               "realizable_full_combination_space": real_full,
               "realizable_n_generated": K * len(real),
               "banking_instances": {k: [i[0] for i in v] for k, v in BANKING_INSTANCES.items()},
               "generated": generated}
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")

    # 예시 출력
    print("\n=== 구체 인스턴스 시나리오 예시 ===")
    for g in generated[:4]:
        flag = " ⚑실행확인" if g["testable"] else ""
        chain = " → ".join(f"{ko(x['sub'])}[{x['instance']}]" for x in g["instances"])
        print(f"\n skeleton: {g['skeleton']}{flag}")
        print(f"   {chain}")
        print(f"   도구: " + " → ".join(x["tool"] for x in g["instances"]))

    # 읽기용 MD
    md = ["# STEP 6 — 인스턴스 조합 (banking)", "",
          f"STEP5 skeleton {len(scen)}개 → 인스턴스 조합 공간(위치별) **{total_full}** · "
          f"skeleton당 K={K} 샘플 = **{len(generated)}개** 구체 시나리오.", "",
          "## banking 서브카테고리별 커버 인스턴스", "",
          "| 서브카테고리 | 인스턴스 (실현 도구) |", "|---|---|"]
    for s, insts in BANKING_INSTANCES.items():
        md.append(f"| {s}({ko(s)}) | " + ", ".join(f"{i[0]}〔{i[1]}〕" for i in insts) + " |")
    md += ["", "## 구체 시나리오 예시 (⚑=실행확인)", ""]
    for i, g in enumerate(generated[:12], 1):
        flag = " ⚑" if g["testable"] else ""
        chain = " → ".join(f"{ko(x['sub'])}[{x['instance']}]" for x in g["instances"])
        md.append(f"{i}. {chain}{flag}")
    OUT_MD.write_text("\n".join(md), encoding="utf-8")
    print(f"\n  → {OUT.relative_to(ROOT)} · {OUT_MD.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
