#!/usr/bin/env python3
"""
STEP 1 (v7 확정): 26 CS 관측 시퀀스 → 2-gram 엣지 추출 + §0 검증

규칙(스펙 §3·§4):
  - 노드 = Subcategory. 2-gram = "연속" 쌍만 (all-pairs 아님).
  - 분기: trunk + 각 branch 를 전개해 경로로. (요약 테이블 파싱 금지)
  - 중복수 counting = trie 방식:
      · 분기가 공유하는 trunk/공통 prefix 는 1회만
      · 같은 CS 내 위치가 다른 진짜 반복은 각각 (CS0037 INV-AT→DAC-UBD ×2)
  - 전제(pre) 노드 포함 · 가능성(◇) 노드 제외 (부록 A 시퀀스에 이미 반영)

검증 기준값(스펙 §0): 활성노드 22 · unique edge 48 · 관측 102 · element 전이 31 · 기본경로 33(동형제거 31)
출력: data/step1_edges.json
"""
import json
from collections import Counter, defaultdict
from pathlib import Path

from sequences_v7 import element_of, expand_flows
from labels import label

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "step1_edges.json"
OUT_MD = ROOT / "data" / "step1_edges.md"


def case_edge_occurrences(flows):
    """한 CS의 flow 목록에서 trie로 엣지 발생수 카운트. {(a,b): count}."""
    trie = {}
    occ = Counter()
    for flow in flows:
        cur = trie
        for i, sub in enumerate(flow):
            if sub not in cur:
                cur[sub] = {}
                if i > 0:
                    occ[(flow[i - 1], sub)] += 1
            cur = cur[sub]
    return occ


def main(expand_branches=True):
    flows_by_case = expand_flows(expand_branches)

    global_occ = Counter()
    evidence = defaultdict(set)
    total_occ = 0
    all_flows = []
    for cid, flows in flows_by_case.items():
        all_flows.extend(tuple(f) for f in flows)
        eo = case_edge_occurrences(flows)
        for e, c in eo.items():
            global_occ[e] += c
            evidence[e].add(cid)
            total_occ += c

    # 노드/엣지/전이 집계
    nodes = sorted({n for f in all_flows for n in f})
    elem_transitions = {(element_of(a), element_of(b)) for (a, b) in global_occ}
    n_flows = len(all_flows)
    n_flows_distinct = len(set(all_flows))

    edges = []
    for (a, b), occ in sorted(global_occ.items(), key=lambda kv: (-len(evidence[kv[0]]), kv[0])):
        edges.append({
            "from": a, "to": b,
            "from_element": element_of(a), "to_element": element_of(b),
            "self_loop": a == b,
            "occurrences": occ,
            "evidence_cs": sorted(evidence[(a, b)]),
            "n_cases": len(evidence[(a, b)]),
        })

    # ── §0 검증 ──
    checks = {
        "활성 노드": (len(nodes), 22),
        "unique edge": (len(edges), 48),   # CS0066 진입 1회 정정(구 49): ENT-II→ENT-II self-edge 소멸
        "관측 합계": (total_occ, 102),      # 구 103 (재배포 분기 정정), 다시 구 104
        "element 전이": (len(elem_transitions), 31),  # 구 32
        "기본 경로(flow)": (n_flows, 33),
        "동형 제거 distinct": (n_flows_distinct, 31),  # 구 32
    }
    print("===== STEP 1 · §0 검증 =====")
    ok = True
    for name, (got, want) in checks.items():
        mark = "✅" if got == want else "❌"
        if got != want:
            ok = False
        print(f"  {mark} {name:20s} 실측 {got:<4d} / 기준 {want}")
    print(f"  {'PASS' if ok else 'FAIL'}  (분기전개={expand_branches})")

    payload = {
        "resolution": "subcategory",
        "expand_branches": expand_branches,
        "validation": {k: {"got": v[0], "want": v[1]} for k, v in checks.items()},
        "n_nodes": len(nodes), "nodes": nodes,
        "n_edges": len(edges), "total_occurrences": total_occ,
        "n_element_transitions": len(elem_transitions),
        "edges": edges,
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")

    # ── 사람이 읽는 Markdown 리포트 ──
    md = ["# STEP 1 — 엣지 추출 (v7)", "",
          f"26개 Case Study 관측 시퀀스에서 뽑은 **연속 2-gram 전이**. "
          f"노드 {len(nodes)}개 · 유니크 엣지 {len(edges)}개 · 관측 {total_occ}회.", "",
          "표기: `코드(한국어)`. 근거 CS = 이 전이가 실제로 관측된 사건.", "",
          "| # | 전이 (from → to) | 근거 CS 수 | 관측 | 근거 사건 |",
          "|---|---|---|---|---|"]
    for i, e in enumerate(edges, 1):
        sl = " ·self" if e["self_loop"] else ""
        md.append(f"| {i} | {label(e['from'])} → {label(e['to'])}{sl} | "
                  f"{e['n_cases']} | {e['occurrences']} | {', '.join(e['evidence_cs'])} |")
    OUT_MD.write_text("\n".join(md), encoding="utf-8")

    print(f"\n  상위 엣지(근거 CS 수):")
    for e in edges[:12]:
        sl = " ·self" if e["self_loop"] else ""
        print(f"    {label(e['from']):22s} → {label(e['to']):24s} CS×{e['n_cases']:<2d} occ={e['occurrences']}{sl}")
    print(f"\n  → {OUT.relative_to(ROOT)}  ·  {OUT_MD.relative_to(ROOT)} (읽기용)")


if __name__ == "__main__":
    import sys
    main(expand_branches="--main-only" not in sys.argv)
