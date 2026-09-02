# -*- coding: utf-8 -*-
"""Clean run 오케스트레이터 — 매 실행마다 산출물을 깨끗이 재생성(stale 파일 잔존 방지).
   (옵션 phase1) → phase2(성립판정) → phase3(goal당 대표 생성) → split(scenarios/ 전체 삭제 후 feasible 만 저장).

   사용:  python run_all.py                # phase2~split (phase1 재사용, 빠름)
          python run_all.py --phase1        # phase1 부터 전부 (gemini 24콜×도메인, 느림)
          python run_all.py --phase1 slack  # 특정 도메인만
"""
import sys, subprocess
from pathlib import Path
import phase2_scenario, gen_pergoal, split_scenarios

HERE = Path(__file__).parent
PY = sys.executable
DOMS = ["banking", "slack", "travel", "workspace"]


def clean_stale():
    """output/ 루트의 옛 개별 P3 산출물 정리(phase1/2 캐시 json 은 재사용하므로 유지)."""
    for f in HERE.glob("output/phase3_*.json"):
        f.unlink()
    for f in HERE.glob("output/pergoal_*.json"):
        f.unlink()


def main(do_phase1, doms):
    clean_stale()
    for d in doms:
        if do_phase1:
            print(f"[{d}] phase1 …", flush=True)
            subprocess.run([PY, str(HERE / "phase1_mapping.py"), d, "gemini"], check=True)
        print(f"[{d}] phase2 …", flush=True)
        phase2_scenario.run(d)
        print(f"[{d}] phase3(대표) …", flush=True)
        gen_pergoal.run(d)
    print("[split] scenarios/ 재정리 …", flush=True)
    split_scenarios.run()
    print("\n=== clean run 완료 ===")


if __name__ == "__main__":
    args = sys.argv[1:]
    do_p1 = "--phase1" in args
    doms = [a for a in args if a in DOMS] or DOMS
    main(do_p1, doms)
