# -*- coding: utf-8 -*-
"""LOO(leave-one-case-out) 일반화 검증 — 그래프가 미관측 사건을 예측하는가.

왜 필요한가
  STEP1~3 은 26 CS 의 관측 시퀀스에서 엣지를 뽑아 경로를 생성한다. "그 26건을 재현한다"는
  건 정의상 당연해서 증거가 못 된다. 진짜 질문은 **못 본 사건도 맞히는가** 다.

무엇을 하는가
  CS_i 를 빼고 나머지 25건으로만 엣지 집합을 재구축한 뒤, 빠진 CS_i 의 실제 관측 경로가
  그 엣지들만으로 구성되는지 본다. 구성되면 = 그 사건을 못 봤어도 생성 가능했다.
  LLM·환경·API 불필요(순수 조합 계산) → 우리 벤치마크를 거치지 않는 외적 타당도 증거라
  순환성 지적에 면역이다.

지표
  exact      전 엣지가 잔여 그래프에 존재 (완전 재현)
  within-1   소실 엣지 1개 이하 (엣지 하나만 더 있었으면 재현)
  결측 엣지  어떤 전이가 그 케이스에만 의존했는지 (= 지식의 단일점 의존)

출력: data/loo_validation.json · data/loo_validation.md
실행: python3 src/loo_validation.py
"""
import json
from collections import Counter

import paths
from sequences_v7 import LINEAR, BRANCH

OUT_JSON = paths.DATA / "loo_validation.json"
OUT_MD = paths.DATA / "loo_validation.md"


def all_flows():
    """케이스 → [경로, ...]. 분기 케이스는 trunk+branch 각각 1경로."""
    flows = {}
    for cs, p in LINEAR.items():
        flows[cs] = [{"label": None, "path": list(p)}]
    for cs, d in BRANCH.items():
        flows[cs] = [{"label": lab, "path": list(d["trunk"]) + list(br)}
                     for lab, br in d["branches"]]
    return flows


def edges_of(paths_):
    return {(a, b) for p in paths_ for a, b in zip(p, p[1:])}


def main():
    flows = all_flows()
    per_case_edges = {cs: edges_of([f["path"] for f in fl]) for cs, fl in flows.items()}
    total_edges = set().union(*per_case_edges.values())

    # 각 엣지를 뒷받침하는 케이스 수 — 1이면 그 케이스 제거 시 소실
    support = Counter()
    for cs, es in per_case_edges.items():
        for e in es:
            support[e] += 1
    singletons = {e for e, c in support.items() if c == 1}

    rows = []
    for cs, fl in flows.items():
        rest = set().union(*(es for c, es in per_case_edges.items() if c != cs))
        for f in fl:
            p = f["path"]
            es = list(zip(p, p[1:]))
            miss = [e for e in es if e not in rest]
            rows.append({
                "case": cs, "branch": f["label"], "path": "→".join(p),
                "len_edges": len(es), "n_missing": len(miss),
                "missing": ["→".join(e) for e in miss],
                "exact": not miss, "within1": len(miss) <= 1,
            })

    n = len(rows)
    exact = sum(r["exact"] for r in rows)
    within1 = sum(r["within1"] for r in rows)
    dist = Counter(r["n_missing"] for r in rows)
    miss_freq = Counter(m for r in rows for m in r["missing"])

    summary = {
        "n_cases": len(flows), "n_flows": n, "n_edges": len(total_edges),
        "n_singleton_edges": len(singletons),
        "exact": exact, "exact_pct": round(100 * exact / n, 1),
        "within1": within1, "within1_pct": round(100 * within1 / n, 1),
        "missing_dist": {str(k): v for k, v in sorted(dist.items())},
    }
    OUT_JSON.write_text(json.dumps({"summary": summary, "flows": rows},
                                   ensure_ascii=False, indent=1), encoding="utf-8")

    md = [
        "# LOO 일반화 검증 — 그래프가 미관측 사건을 예측하는가", "",
        "케이스 하나를 빼고 나머지 25건으로 엣지를 재구축한 뒤, **빠진 케이스의 실제 관측 경로가 "
        "그 엣지들만으로 구성되는지** 본다. 구성되면 그 사건을 못 봤어도 생성 가능했다는 뜻.",
        "LLM·환경 불필요(순수 조합) → 우리 벤치마크를 거치지 않는 외적 타당도 증거.", "",
        "## 결과", "",
        f"- 케이스 **{summary['n_cases']}** · 경로(flow) **{n}** · 엣지 **{len(total_edges)}**",
        f"- **완전 재현(exact): {exact}/{n} = {summary['exact_pct']}%**",
        f"- **1엣지 이내(within-1): {within1}/{n} = {summary['within1_pct']}%**",
        f"- 단일 케이스만 뒷받침하는 엣지: **{len(singletons)}/{len(total_edges)}** "
        f"— 이 엣지들이 LOO 실패의 직접 원인이다.", "",
        "소실 엣지 수 분포: " + " · ".join(f"`{k}개` {v} flow" for k, v in sorted(dist.items())), "",
        "## 케이스별", "",
        "| 케이스 | 분기 | 경로 | 엣지 | 소실 | 판정 |",
        "|---|---|---|---|---|---|",
    ]
    for r in sorted(rows, key=lambda x: (x["n_missing"], x["case"])):
        v = "✅ exact" if r["exact"] else ("△ within-1" if r["within1"] else "❌")
        md.append(f"| {r['case']} | {r['branch'] or '-'} | `{r['path']}` | "
                  f"{r['len_edges']} | {r['n_missing']} | {v} |")
    md += ["", "## 가장 자주 소실된 전이", "",
           "그 케이스에만 의존해 다른 사건으로부터는 복원되지 않는 전이 = 지식의 단일점.", "",
           "| 전이 | 소실 flow 수 |", "|---|---|"]
    for e, c in miss_freq.most_common(15):
        md.append(f"| `{e}` | {c} |")
    OUT_MD.write_text("\n".join(md), encoding="utf-8")

    print(f"케이스 {summary['n_cases']} · flow {n} · 엣지 {len(total_edges)} "
          f"(단일근거 {len(singletons)})")
    print(f"완전 재현 {exact}/{n} = {summary['exact_pct']}%")
    print(f"1엣지 이내 {within1}/{n} = {summary['within1_pct']}%")
    print(f"저장: {OUT_MD.name} · {OUT_JSON.name}")


if __name__ == "__main__":
    main()
