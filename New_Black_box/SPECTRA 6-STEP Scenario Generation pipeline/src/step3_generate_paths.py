#!/usr/bin/env python3
"""
STEP 3 (v7): 경로(시나리오) 생성 — 그래프 walk

정책(스펙 §6):
  - 종점 '도달' walk만 (미완성 제외). 길이 무관(2노드 CS0040도 완성).
  - max_depth = 7 (최장 관측 CS 노드수, 상한. 평균 아님)
  - 사이클 허용 + 노드별 반복 상한(실제 관측 최대):
        INV-AT ≤3 · ENT-II ≤2 · DAC-UBD ≤2 · HD-UI ≤2 · 나머지 ≤1

시작 정책(start_policy):
  - "observed4"  : 관측된 첫 노드 4개 (스펙 §6 기준값 = 1,324 검증용)
  - "broad"      : out-edge가 있는 모든 노드 (STEP4 이전엔 시작을 안 가림 — 사용자 방침)
                   → 부적절한 시작(진입/편입 아님)은 STEP4 rule이 삭제
출력: data/step3_paths.json
"""
import json
from pathlib import Path

from sequences_v7 import expand_flows
from labels import path_str

ROOT = Path(__file__).resolve().parent.parent
GRAPH = ROOT / "data" / "step2_graph.json"
OUT = ROOT / "data" / "step3_paths.json"
OUT_MD = ROOT / "data" / "step3_paths.md"

# 노드별 반복 상한 = 실제 관측 최대. 최댓값은 3(INV-AT). 나머지 2, 그 외 1. (일괄 3 아님)
CAPS = {"INV-AT": 3, "ENT-II": 2, "DAC-UBD": 2, "HD-UI": 2}   # 기본 1
MAX_DEPTH = 7   # 노드 수 상한 = 최장 관측 CS


def cap(n):
    return CAPS.get(n, 1)


def generate(starts, terminals, adj, emit_all=False):
    """emit_all=False: 관측 종점 도달만 (스펙 §6 검증용).
       emit_all=True : 완성 판정 없이 모든 walk (종점 판단은 STEP4 위임 — 확정 방침)."""
    terminals = set(terminals)
    paths = set()

    def dfs(path, counts):
        node = path[-1]
        if len(path) >= 2 and (emit_all or node in terminals):
            paths.add(tuple(path))
        if len(path) >= MAX_DEPTH:
            return
        for nxt in adj.get(node, []):
            if counts.get(nxt, 0) < cap(nxt):
                counts[nxt] = counts.get(nxt, 0) + 1
                path.append(nxt)
                dfs(path, counts)
                path.pop()
                counts[nxt] -= 1

    for s in starts:
        dfs([s], {s: 1})
    return paths


def main():
    g = json.loads(GRAPH.read_text(encoding="utf-8"))
    adj = g["adjacency"]
    nodes = g["nodes"]
    terminals = g["terminal_nodes"]
    observed4 = g["observed_first"]                    # 참고: 실제 사건 첫 노드(스펙 검증용)
    broad = g["start_candidates"]                       # 시작 후보 = out-edge 있는 노드 전부

    # 관측 flow 집합(기본 31 = distinct observed)
    observed_flows = {tuple(f) for fs in expand_flows(True).values() for f in fs}

    results = {}
    for policy, starts, emit_all in [("observed4", observed4, False), ("broad", broad, True)]:
        paths = generate(starts, terminals, adj, emit_all)
        base = paths & observed_flows           # 관측 재현분
        ext = paths - observed_flows            # 신규 조합
        lens = [len(p) for p in paths]
        results[policy] = {
            "n_starts": len(starts), "starts": starts,
            "total": len(paths), "base_observed": len(base), "extended": len(ext),
            "len_min": min(lens), "len_max": max(lens),
            "len_avg": round(sum(lens) / len(lens), 2),
        }

    # ── §6 검증 (observed4 기준) ──
    o = results["observed4"]
    checks = {
        "전체 경로": (o["total"], 1324),   # CS0066 진입 1회 정정(구 1589)
        "기본(관측)": (o["base_observed"], 31),  # 구 32
        "확장": (o["extended"], 1293),      # 구 1557
    }
    print("===== STEP 3 · §6 검증 (start=observed4) =====")
    ok = True
    for name, (got, want) in checks.items():
        mark = "✅" if got == want else "❌"
        ok &= got == want
        print(f"  {mark} {name:12s} 실측 {got:<6d} / 기준 {want}")
    print(f"  {'PASS' if ok else 'FAIL'}  · 길이 {o['len_min']}~{o['len_max']} 평균 {o['len_avg']}")

    b = results["broad"]
    print(f"\n===== STEP 3 · broad (start={b['n_starts']} : out-edge 있는 노드 전부) =====")
    print(f"  시작 노드: {', '.join(b['starts'])}")
    print(f"  전체 {b['total']} (관측재현 {b['base_observed']} + 신규 {b['extended']}) · "
          f"길이 {b['len_min']}~{b['len_max']} 평균 {b['len_avg']}")
    print(f"  → observed4 대비 {b['total']-o['total']:+d}개 (STEP4에서 부적절 시작 삭제 예정)")

    broad_path_set = generate(broad, terminals, adj, emit_all=True)
    broad_paths = sorted(broad_path_set)
    payload = {"caps": CAPS, "max_depth": MAX_DEPTH,
               "validation_observed4": {k: {"got": v[0], "want": v[1]} for k, v in checks.items()},
               "policies": results,
               "broad_paths": ["→".join(p) for p in broad_paths]}
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")

    # ── 읽기용 Markdown: 관측 32 + 신규 예시 ──
    md = ["# STEP 3 — 경로(시나리오) 생성 (v7)", "",
          f"시작 정책=broad({b['n_starts']} 노드) · 종점 도달 walk · 사이클 허용+반복상한 · 최대 7노드.",
          f"전체 **{b['total']}** = 관측재현 {b['base_observed']} + 신규 {b['extended']}. (참고: 시작을 관측 4개로 "
          f"좁히면 {o['total']}개)", "",
          "표기: `코드(한국어)`.", "",
          "## 실제 관측된 공격 흐름 31개 (기본)", ""]
    for i, f in enumerate(sorted(observed_flows), 1):
        md.append(f"{i}. {path_str(f)}")
    md += ["", "## 새로 조합된 시나리오 예시 20개 (신규)", ""]
    ext_examples = [p for p in broad_paths if p not in observed_flows][:20]
    for i, f in enumerate(ext_examples, 1):
        md.append(f"{i}. {path_str(f)}")

    # 반복(툴루프·재진입) 포함 경로 예시
    from collections import Counter
    rep_paths = [p for p in broad_paths if any(v > 1 for v in Counter(p).values())]
    md += ["", f"## 반복 노드가 들어간 경로 — 전체 {len(rep_paths)}개 (전체의 "
           f"{len(rep_paths) * 100 // len(broad_paths)}%)", ""]
    for tag, filt in [("INV-AT 3회 (툴루프)", lambda p: p.count("INV-AT") >= 3),
                      ("ENT-II 2회 (재진입)", lambda p: p.count("ENT-II") >= 2),
                      ("HD-UI 2회 (사용자 유도 반복)", lambda p: p.count("HD-UI") >= 2)]:
        ex = [p for p in broad_paths if filt(p)]
        md.append(f"**{tag}** — {len(ex)}개")
        for f in ex[:2]:
            md.append(f"- {path_str(f)}")
        md.append("")
    OUT_MD.write_text("\n".join(md), encoding="utf-8")

    print(f"\n  관측 흐름 예시(한국어):")
    for f in sorted(observed_flows)[:5]:
        print("    " + path_str(f))
    print(f"\n  → {OUT.relative_to(ROOT)}  ·  {OUT_MD.relative_to(ROOT)} (읽기용)")


if __name__ == "__main__":
    main()
