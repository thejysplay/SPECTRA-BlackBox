#!/bin/bash
# 범용 noVNC 로그인 스택 기동 (서버, sudo 불필요).
# 사전 1회: sudo apt-get install -y xvfb x11vnc novnc websockify openbox fonts-noto-cjk
# 사용: bash Inspection/novnc_up.sh <URL> <PROFILE_DIR>
#   예: bash Inspection/novnc_up.sh https://www.genspark.ai/ .spectra_sessions/genspark
set -u
SB="$(cd "$(dirname "$0")/.." && pwd)"
VENV="$SB/Agent/damn-vulnerable-llm-agent/blackbox/bin/python"
URL="${1:?URL 필요}"
PROFILE="${2:?PROFILE 경로 필요}"
LOG="$SB/.spectra_sessions/novnc.log"
export DISPLAY=:99
cd "$SB"
mkdir -p "$SB/.spectra_sessions"
: > "$LOG"

echo "[up] 기존 잔여 정리" | tee -a "$LOG"
pkill -f "novnc_login.py"       2>/dev/null || true
pkill -f "Xvfb :99"             2>/dev/null || true
pkill -f "x11vnc -display :99"  2>/dev/null || true
pkill -f "websockify.*6080"     2>/dev/null || true
pkill -f "openbox"              2>/dev/null || true
sleep 2

nohup Xvfb :99 -screen 0 1440x900x24 -nolisten tcp >>"$LOG" 2>&1 &
sleep 2
nohup openbox >>"$LOG" 2>&1 &
sleep 1
nohup x11vnc -display :99 -localhost -rfbport 5900 -forever -shared -nopw >>"$LOG" 2>&1 &
sleep 1
NOVNC_WEB=/usr/share/novnc
[ -d "$NOVNC_WEB" ] || NOVNC_WEB=$(dirname "$(find /usr/share -name vnc.html 2>/dev/null | head -1)")
nohup websockify --web="$NOVNC_WEB" 127.0.0.1:6080 localhost:5900 >>"$LOG" 2>&1 &
sleep 2

echo "[up] 포트:" | tee -a "$LOG"; ss -ltn 2>/dev/null | grep -E ':(5900|6080)' | tee -a "$LOG"
echo "[up] 로컬: ssh -L 6080:localhost:6080 -p 8080 kitesu@<서버> → http://localhost:6080/vnc.html?autoconnect=true&resize=scale" | tee -a "$LOG"
echo "[up] URL=$URL  PROFILE=$PROFILE  (로그: $LOG)" | tee -a "$LOG"
exec "$VENV" "$SB/Inspection/novnc_login.py" --url "$URL" --profile "$PROFILE" 2>&1 | tee -a "$LOG"
