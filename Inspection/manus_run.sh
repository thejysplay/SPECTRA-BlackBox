#!/bin/bash
# Manus 에이전트 어댑터를 Xvfb headed로 실행 (Manus는 헤드리스/봇 차단).
# 전제: .spectra_sessions/manus 로그인 세션(noVNC로 1회 로그인).
#       로그인 noVNC 스택 떠 있으면 먼저: bash Inspection/novnc_down.sh .spectra_sessions/manus
# 사용: bash Inspection/manus_run.sh --message "프롬프트" --out out.json --timeout 600
set -u
SB=/home/kitesu/SPECTRA-BlackBox
VENV="$SB/Agent/damn-vulnerable-llm-agent/blackbox/bin/python"
export DISPLAY=:99
cd "$SB"
if ! pgrep -x Xvfb >/dev/null 2>&1; then
  nohup Xvfb :99 -screen 0 1440x1000x24 -nolisten tcp >/tmp/xvfb_manus.log 2>&1 &
  sleep 3
fi
pgrep -x Xvfb >/dev/null 2>&1 || { echo "Xvfb 기동 실패"; exit 1; }
exec "$VENV" "$SB/Inspection/manus_agent.py" "$@"
