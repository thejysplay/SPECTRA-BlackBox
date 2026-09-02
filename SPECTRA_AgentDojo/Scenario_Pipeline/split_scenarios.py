# -*- coding: utf-8 -*-
"""도메인별 폴더에 파이프라인 산출물 전부 정리.
   output/scenarios/{domain}/
     ├ phase1_mapping.json       (P1: Agent Spec × Threat Instance 매핑 결과)
     ├ phase2_feasibility.json   (P2: Compatibility Gate 성립판정 + Family/Variant)
     ├ {goal}_{critical}.json     (P3: goal당 대표 시나리오 1개 — 전체 corpus 중 샘플)
     └ _index.json               (성립/탈락 목표 요약 + 파일 인덱스)"""
import json, re, shutil
from pathlib import Path

HERE = Path(__file__).parent
SRC = HERE / "output"
DST = HERE / "output" / "scenarios"
DOMS = ["banking", "slack", "travel", "workspace"]

# Goal 짧은 한글 태그 (파일명·인덱스 식별용 — G 코드만으로 뭔지 모르는 문제 해결)
GOAL_TAG = {
    "G1": "데이터유출", "G2": "코드실행", "G3": "사용자조작", "G4": "지속오염",
    "G5": "자격증명침해", "G6": "비의도민감작업", "G7": "시스템파괴", "G8": "무결성침해", "G9": "C2",
}


def gtag(gid):
    return f"{gid} {GOAL_TAG.get(gid, '')}".strip()


def safe(s):
    return re.sub(r"[^A-Za-z0-9_]+", "_", s or "")[:40]


def run():
    tree = {}
    for d in DOMS:
        ddir = DST / d
        if ddir.exists():
            shutil.rmtree(ddir)                      # 옛 파일(폐기된 goal 등) 정리
        ddir.mkdir(parents=True, exist_ok=True)

        # P1·P2 결과 복사
        shutil.copy(SRC / f"phase1_{d}_gemini.json", ddir / "phase1_mapping.json")
        p2 = json.loads((SRC / f"phase2_{d}.json").read_text(encoding="utf-8"))
        (ddir / "phase2_feasibility.json").write_text(json.dumps(p2, ensure_ascii=False, indent=2), encoding="utf-8")

        # P2 성립/탈락 요약 (한글 이름 병기)
        feasible, dropped = [], {}
        for gid, gr in p2["goals"].items():
            if gr.get("families"):
                feasible.append(gtag(gid))
            elif not gr.get("gate1"):
                dropped[gtag(gid)] = f"Gate1 없는 Element {gr.get('missing')}"
            elif gr.get("compat") is False:
                dropped[gtag(gid)] = f"Compat: {gr.get('reason')}"
            else:
                dropped[gtag(gid)] = "Gate2: impact 실현 tool 없음"

        # P3 대표 시나리오 → 개별 파일
        data = json.loads((SRC / f"pergoal_{d}.json").read_text(encoding="utf-8"))
        scen_index = []
        for r in data:
            gid, ct = r["goal"], safe(r["critical_tool"].strip("()"))
            fn = f"{gid}_{GOAL_TAG.get(gid, '')}_{ct}.json"
            sc = r.get("scenario", {}) or {}
            if isinstance(sc, dict):
                sc.pop("goal", None)                      # 바깥 goal 과 중복 → 본문에서 제거
            (ddir / fn).write_text(json.dumps({
                "domain": d, "goal": gid, "goal_label": gtag(gid),
                "critical_tool": r["critical_tool"],
                "scenario": sc,
            }, ensure_ascii=False, indent=2), encoding="utf-8")
            scen_index.append({"goal": gid, "goal_label": gtag(gid),
                               "critical_tool": r["critical_tool"], "file": fn,
                               "summary": sc.get("summary", "") if isinstance(sc, dict) else ""})

        (ddir / "_index.json").write_text(json.dumps({
            "domain": d,
            "available_elements": p2["available_elements"],
            "feasible_goals": feasible,
            "dropped_goals": dropped,
            "files": {"phase1": "phase1_mapping.json", "phase2": "phase2_feasibility.json"},
            "scenarios": scen_index,
        }, ensure_ascii=False, indent=2), encoding="utf-8")
        tree[d] = {"feasible": feasible, "files": [f.name for f in sorted(ddir.iterdir())]}
    return tree


if __name__ == "__main__":
    tree = run()
    print(f"저장 위치: {DST}\n")
    for d, info in tree.items():
        print(f"  {d}/  성립목표 = {info['feasible']}")
        for f in info["files"]:
            print(f"     {f}")
        print()
