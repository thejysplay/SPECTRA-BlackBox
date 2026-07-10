#!/bin/bash
# 범용 noVNC 스택 종료 (프로필 보존). 어댑터 실행 전 반드시 내려야 프로필 잠금이 풀린다.
# 사용: bash Inspection/novnc_down.sh [PROFILE_DIR]   (PROFILE 주면 Singleton 잠금까지 정리)
pkill -f "novnc_login.py"       2>/dev/null || true
pkill -f "Xvfb :99"             2>/dev/null || true
pkill -f "x11vnc -display :99"  2>/dev/null || true
pkill -f "websockify.*6080"     2>/dev/null || true
pkill -f "openbox"              2>/dev/null || true
sleep 2
[ -n "${1:-}" ] && rm -f "$1"/Singleton* 2>/dev/null || true
echo "[down] noVNC 스택 종료 완료 (프로필 보존)"
