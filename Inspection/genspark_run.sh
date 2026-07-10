#!/bin/bash
# Genspark 슈퍼에이전트 어댑터를 Xvfb headed로 실행 (Genspark은 headless 차단).
# 전제: .spectra_sessions/genspark 에 로그인 세션 있음(noVNC로 1회 로그인).
#       로그인 noVNC 스택이 떠 있으면 먼저 novnc_down.sh 로 내릴 것(프로필 잠금).
# 사용: bash Inspection/genspark_run.sh --message "질문" --out out.json --timeout 300
set -u
SB="$(cd "$(dirname "$0")/.." && pwd)"
VENV="$SB/Agent/damn-vulnerable-llm-agent/blackbox/bin/python"
export DISPLAY=:99
cd "$SB"

# Xvfb :99 없으면 기동 (pkill 미사용 — 기존 로그인스택 Xvfb 보호)
if ! pgrep -x Xvfb >/dev/null 2>&1; then
  nohup Xvfb :99 -screen 0 1440x1000x24 -nolisten tcp >/tmp/xvfb_genspark.log 2>&1 &
  sleep 3
fi
pgrep -x Xvfb >/dev/null 2>&1 || { echo "Xvfb 기동 실패"; exit 1; }

exec "$VENV" "$SB/Inspection/genspark_agent.py" "$@"
