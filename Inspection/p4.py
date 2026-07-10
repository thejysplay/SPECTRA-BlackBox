#!/usr/bin/env python3
"""SPECTRA-BlackBox P4 — 실행+수집.

P3 시나리오(scenarios.yaml)를 adapter로 대상에 멀티턴 실행하고 trace를 수집한다.
P1의 collect와 같은 메커니즘(발화 → adapter → 관측 수집) — 입력만 공격 시나리오라는 점이 다르다.
대상 무관: adapter만 교체하면 streamlit/API/CLI 어디든.

입력:  --scenarios scenarios.yaml + --url
출력:  traces.jsonl (P5가 판정)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import asdict
from pathlib import Path

import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from adapter import make_adapter   # noqa: E402

DEFAULT_URL = "http://localhost:5501"


def execute(scenarios: list, url: str, headless: bool, proto: str = "auto") -> list:
    """각 시나리오를 한 세션에서 멀티턴 실행 → trace. (시나리오 사이엔 reset)
    proto(mcp/a2a/auto)로 어댑터 선택 — 프로토콜 차이는 adapter 층이 흡수."""
    traces = []
    with make_adapter(url, headless, proto=proto) as ad:
        for sc in scenarios:
            ad.reset()
            turn_obs = []
            try:
                for t in sc.get("turns", []):
                    obs = ad.send(t.get("user_input", ""))
                    turn_obs.append({"role": t.get("role"), "q": t.get("user_input"), **asdict(obs)})
            except Exception as e:
                turn_obs.append({"error": f"{type(e).__name__}: {e}"})
            traces.append({"scenario_id": sc.get("scenario_id"), "source_id": sc.get("source_id"),
                           "strategy": sc.get("strategy"), "turns": turn_obs})
            print(f"  [exec] {sc.get('scenario_id')}: {len(turn_obs)}턴")
    return traces


def main() -> None:
    ap = argparse.ArgumentParser(description="P4 실행+수집 (시나리오 → adapter → traces)")
    ap.add_argument("--scenarios", required=True, help="P3 출력 scenarios.yaml")
    ap.add_argument("--url", default=DEFAULT_URL)
    ap.add_argument("--out", required=True)
    ap.add_argument("--headed", action="store_true")
    ap.add_argument("--proto", default=None,
                    help="전송 어댑터 오버라이드(goover/streamlit/api/mcp/a2a). "
                         "미지정 시 scenarios.yaml의 proto 사용")
    a = ap.parse_args()

    doc = yaml.safe_load(Path(a.scenarios).read_text(encoding="utf-8"))
    scens = doc.get("scenarios", [])
    # 전송(transport)은 실행 시점의 런타임 관심사 — CLI --proto가 있으면 그것이 우선.
    # (P3는 profile.modality를 proto로 기록하므로 chat이 되는데, goover는 브라우저 어댑터가 필요)
    proto = a.proto or doc.get("proto", "auto")
    print(f"[p4] {len(scens)}시나리오 실행 @ {a.url} (proto={proto})")
    traces = execute(scens, a.url, not a.headed, proto=proto)

    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    (out / "traces.jsonl").write_text(
        "\n".join(json.dumps(t, ensure_ascii=False) for t in traces), encoding="utf-8")
    print(f"[p4] {len(traces)}trace → {out}/traces.jsonl")


if __name__ == "__main__":
    main()
