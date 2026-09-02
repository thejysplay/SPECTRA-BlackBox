# -*- coding: utf-8 -*-
"""도메인별 시나리오 생성 — 각 feasible goal 당 '대표 1개'.
   대표 family 선택: (1) human(G3)  (2) read-only 아닌 critical  (3) 폴백 first.
   (전체 critical 도구별 전개는 아직 하지 않음 — 대표만.)"""
import json, sys
from pathlib import Path
import yaml
import knowledge, phase3_scenario as P3

HERE = Path(__file__).parent
AGENT = HERE.parent / "Agent_Specification"
RO = ("get_", "read_", "search_", "list_", "check_", "view_")


def is_ro(t):
    return bool(t) and t.startswith(RO)


def pick_family(gr):
    fams = gr.get("families", [])
    for f in fams:                                   # G3 human
        if f["critical_action"] is None:
            return f
    clean = [f for f in fams if not is_ro(f["critical_action"]["tool"])]
    if clean:
        return clean[0]
    return fams[0] if fams else None


def run(domain, model="gemini"):
    K = knowledge.load()
    spec = yaml.safe_load((AGENT / f"AgentSPEC_{domain}.yaml").read_text(encoding="utf-8"))
    p2 = json.loads((HERE / "output" / f"phase2_{domain}.json").read_text(encoding="utf-8"))
    out = []
    for gid, gr in p2["goals"].items():
        if not gr.get("families"):
            continue
        fam = pick_family(gr)
        if not fam:
            continue
        v = fam["variants"][0] if fam.get("variants") else None
        ct = (fam["critical_action"] or {}).get("tool")
        sc = P3.generate(spec, K, fam, variant=v, model=model)
        errs = P3.validate_scenario(sc, fam)
        out.append({"goal": gid, "goal_name": fam["goal_name"], "critical_tool": ct or "(human)",
                    "scenario": sc})
        print(f"  {gid} {fam['goal_name']:16s} critical={ct or '(human)':32s} {'✓' if not errs else '⚠'+str(errs)}", flush=True)
    outp = HERE / "output" / f"pergoal_{domain}.json"
    outp.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"저장: {outp} ({len(out)}건)")
    return out


if __name__ == "__main__":
    run(sys.argv[1] if len(sys.argv) > 1 else "banking")
