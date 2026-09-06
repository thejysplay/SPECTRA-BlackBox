#!/usr/bin/env python3
"""
STEP 2 (v7 확정): 인접 그래프 구성 + §5 검증

입력: data/step1_edges.json (48 엣지, 근거 CS 포함) · sequences_v7 (시작/종점 산출)
출력: data/step2_graph.json  (adjacency list + 그래프 속성)

노드 = Subcategory 22개. 방향 그래프. DAG 아님(사이클 존재).
시작/종점은 in/out-degree가 아니라 '실제 CS의 첫/끝 노드' 집합으로 정의(→ STEP3 경로용).

§5 기준값: 22노드·48엣지·element전이 31 · 시작 4·종점 10 · self-loop 1(HD-UI) · 2-cycle 4
          · DAG 아님(위상정렬 3 / 사이클 19) · density 48/462≈10%
"""
import json
from collections import defaultdict, deque
from pathlib import Path

from sequences_v7 import element_of, expand_flows
from labels import label

ROOT = Path(__file__).resolve().parent.parent
EDGES_IN = ROOT / "data" / "step1_edges.json"
OUT = ROOT / "data" / "step2_graph.json"
OUT_MD = ROOT / "data" / "step2_graph.md"


def main():
    step1 = json.loads(EDGES_IN.read_text(encoding="utf-8"))
    edges = step1["edges"]
    nodes = step1["nodes"]

    out_adj = defaultdict(list)   # node -> [(to, n_cases, evidence)]
    in_adj = defaultdict(list)
    edge_ev = {}
    indeg = {n: 0 for n in nodes}
    outdeg = {n: 0 for n in nodes}
    for e in edges:
        a, b = e["from"], e["to"]
        out_adj[a].append(b)
        in_adj[b].append(a)
        edge_ev[(a, b)] = e["evidence_cs"]
        indeg[b] += 1
        outdeg[a] += 1

    # ── 그래프 구조상 시작 후보 / 막다른 노드 (rule 이전) ──
    #   시작 후보(source) = out-edge가 있는 모든 노드 → 인접 리스트의 '키'.
    #   sink = out-edge가 없는 노드(더 갈 데 없음).
    sources = sorted([n for n in nodes if outdeg[n] > 0])   # 시작 후보
    sinks = sorted([n for n in nodes if outdeg[n] == 0])     # 막다른

    # (참고용) 실제 26 사건에서 관측된 첫/끝 노드 — 스펙 §5 대조용, 시작 제한 아님
    flows = [f for fs in expand_flows(True).values() for f in fs]
    obs_first = sorted({f[0] for f in flows})
    obs_last = sorted({f[-1] for f in flows})
    starts, terminals = sources, obs_last  # 하위호환(payload 필드용)

    # self-loop
    self_loops = sorted([n for n in nodes if n in out_adj.get(n, [])])
    # 양방향 2-cycle (a<b, a→b 와 b→a 둘 다)
    edge_set = set(edge_ev)
    two_cycles = []
    for (a, b) in edge_set:
        if a < b and (b, a) in edge_set:
            # 스펙 표기 = 양방향 근거 CS 합집합(재진입/tool-loop 계열 전체)
            ev = sorted(set(edge_ev[(a, b)]) | set(edge_ev[(b, a)]))
            two_cycles.append({"pair": [a, b], "evidence_cs": ev})
    two_cycles.sort(key=lambda x: x["pair"])

    # Kahn 위상정렬 (self-loop 노드는 절대 제거 안 됨 → 사이클로 카운트)
    ind = dict(indeg)
    q = deque([n for n in nodes if ind[n] == 0])
    order = []
    while q:
        n = q.popleft()
        order.append(n)
        for m in out_adj.get(n, []):
            if m == n:
                continue
            ind[m] -= 1
            if ind[m] == 0:
                q.append(m)
    n_sorted = len(order)
    n_cyclic = len(nodes) - n_sorted

    elem_transitions = sorted({(element_of(a), element_of(b)) for (a, b) in edge_set})

    # 허브
    hubs = {
        "ENT-II_out": len(set(out_adj.get("ENT-II", []))),
        "INV-AT_in": len(set(in_adj.get("INV-AT", []))),
        "INV-AT_out": len(set(out_adj.get("INV-AT", []))),
        "ID-ER_in": len(set(in_adj.get("ID-ER", []))),
    }
    density = len(edge_set) / (len(nodes) * (len(nodes) - 1))

    # ── §5 검증 ──
    checks = {
        "노드": (len(nodes), 22),
        "엣지": (len(edge_set), 48),                 # CS0066 진입 1회 정정(구 49)
        "element 전이": (len(elem_transitions), 31),  # 구 32
        "self-loop": (len(self_loops), 1),            # 구 2 → HD-UI만 (ENT-II self-edge 소멸)
        "2-cycle": (len(two_cycles), 4),
        "위상정렬 노드": (n_sorted, 3),
        "사이클 노드": (n_cyclic, 19),
        "관측 시작(첫노드)": (len(obs_first), 4),   # 참고: 실제 사건, 시작 제한 아님
        "관측 종점(끝노드)": (len(obs_last), 10),
    }
    print("===== STEP 2 · §5 검증 =====")
    ok = True
    for name, (got, want) in checks.items():
        mark = "✅" if got == want else "❌"
        ok &= got == want
        print(f"  {mark} {name:16s} 실측 {got:<4d} / 기준 {want}")
    print(f"  {'PASS' if ok else 'FAIL'}")
    print(f"\n  ▶ 시작 후보(source, out-edge 보유) {len(sources)}개 — rule 이전엔 전부 시작 가능:")
    print(f"     {', '.join(label(s) for s in sources)}")
    print(f"  ▶ sink(막다른, out-edge 없음) {len(sinks)}개: {', '.join(label(s) for s in sinks)}")
    print(f"  self-loop: {', '.join(label(s) for s in self_loops)}")
    print("  2-cycle:")
    for tc in two_cycles:
        print(f"    {label(tc['pair'][0])} ⇄ {label(tc['pair'][1])}  {tc['evidence_cs']}")
    print(f"  허브: ENT-II out={hubs['ENT-II_out']} · "
          f"INV-AT in={hubs['INV-AT_in']}/out={hubs['INV-AT_out']} · ID-ER in={hubs['ID-ER_in']}")
    print(f"  density: {len(edge_set)}/{len(nodes)*(len(nodes)-1)} = {density:.1%}")
    print(f"  (참고) 실제 사건 관측 첫노드 {len(obs_first)} / 끝노드 {len(obs_last)} — 시작 제한 아님")

    # ── 읽기용 Markdown (인접 리스트 중심) ──
    md = ["# STEP 2 — 인접 그래프 (v7)", "",
          f"2-gram 엣지 {len(edge_set)}개로 만든 인접 리스트. 노드 {len(nodes)}개 · DAG 아님(사이클 {n_cyclic}).", "",
          "## 인접 리스트 (각 노드 → 올 수 있는 다음 노드)",
          "각 줄의 **왼쪽 노드**가 곧 시작 후보(rule 이전엔 전부 시작 가능).", ""]
    for n in sources:
        nxts = sorted(set(out_adj.get(n, [])))
        md.append(f"- **{label(n)}** → " + ", ".join(label(x) for x in nxts))
    md += ["",
           f"## 시작 후보 (source, out-edge 보유) — {len(sources)}개",
           "rule로 안 막으면 이 전부가 시작이 될 수 있음.",
           "".join(f"\n- {label(s)}" for s in sources),
           f"\n## sink (막다른 노드, out-edge 없음) — {len(sinks)}개",
           "".join(f"\n- {label(s)}" for s in sinks),
           "\n## self-loop / 2-cycle (사이클 구조)",
           "".join(f"\n- self: {label(s)}" for s in self_loops),
           "".join(f"\n- cycle: {label(tc['pair'][0])} ⇄ {label(tc['pair'][1])} · 근거 {', '.join(tc['evidence_cs'])}"
                   for tc in two_cycles),
           f"\n---\n참고: 실제 26 사건에서 관측된 첫 노드 {len(obs_first)}개·끝 노드 {len(obs_last)}개는 "
           "'사실'일 뿐 시작/종점 제한이 아님(제한은 STEP 4 rule)."]
    OUT_MD.write_text("\n".join(md), encoding="utf-8")

    payload = {
        "n_nodes": len(nodes), "n_edges": len(edge_set),
        "validation": {k: {"got": v[0], "want": v[1]} for k, v in checks.items()},
        "nodes": nodes,
        "adjacency": {n: sorted(set(out_adj.get(n, []))) for n in nodes},
        "in_degree": indeg, "out_degree": outdeg,
        "start_candidates": sources, "sinks": sinks,
        "observed_first": obs_first, "observed_last": obs_last,
        "terminal_nodes": obs_last,   # STEP3 완성 판정 기준(현재는 관측 종점)
        "self_loops": self_loops, "two_cycles": two_cycles,
        "is_dag": n_cyclic == 0, "topo_sortable": n_sorted, "cyclic_nodes": n_cyclic,
        "hubs": hubs, "density": density,
        "element_transitions": [list(t) for t in elem_transitions],
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n  → {OUT.relative_to(ROOT)}  ·  {OUT_MD.relative_to(ROOT)} (읽기용)")


if __name__ == "__main__":
    main()
