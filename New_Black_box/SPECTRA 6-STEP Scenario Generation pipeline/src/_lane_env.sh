#!/usr/bin/env bash
# 레인 스크립트 공통 환경. 각 스크립트 첫머리에서 source 한다.
# 하드코딩된 /home/kitesu 절대경로를 대체 — 스크립트 위치에서 역산한다.
#
# 덮어쓰기용 환경변수:
#   SPECTRA_PY          사용할 python 실행파일 (기본: agentdojo .venv → 없으면 python3)
#   SPECTRA_AGENTDOJO   개조 AgentDojo 루트 (paths.py 와 동일 규칙)

_LANE_SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PIPE_ROOT="$(dirname "$_LANE_SRC")"
REPO_ROOT="$(dirname "$(dirname "$PIPE_ROOT")")"
cd "$PIPE_ROOT"

ADOJO="${SPECTRA_AGENTDOJO:-$REPO_ROOT/SPECTRA_AgentDojo/agentdojo}"

if [ -n "${SPECTRA_PY:-}" ]; then
  PY="$SPECTRA_PY"
elif [ -x "$ADOJO/.venv/bin/python" ]; then
  PY="$ADOJO/.venv/bin/python"
else
  PY="$(command -v python3)"
  echo "[경고] agentdojo .venv 없음 → $PY 사용. 'cd $ADOJO && uv sync' 로 만드는 게 정상 경로." >&2
fi

declare -A TOT=([banking]=144 [travel]=141 [slack]=108)
