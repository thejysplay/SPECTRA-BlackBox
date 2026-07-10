#!/bin/bash
# Manus 에이전트 P1~P5 파이프라인 (v8). 결과: Output/new/Manus/
# ⚠️ Manus는 헤드리스/봇 차단 → Xvfb 가상화면에 headed로 실행(이 스크립트가 DISPLAY 세팅).
# 전제: .spectra_sessions/manus 로그인 세션(noVNC로 1회 로그인).
#       로그인 noVNC 스택 떠 있으면 먼저: bash Inspection/novnc_down.sh .spectra_sessions/manus
# ⚠️ Manus는 자율 에이전트라 probe당 수 분 소요·크레딧 소모 큼(무료 플랜 주의).
set -u
SB=/home/kitesu/SPECTRA-BlackBox
PY=$SB/Agent/damn-vulnerable-llm-agent/blackbox/bin/python
cd "$SB/Inspection"
URL="https://manus.im/app"
OUT="$SB/Output/new/Manus"
F='fastapi|litellm_logging|proxy_server|Traceback|File "|raise ImportError|ModuleNotFound|During handling|^[[:space:]]*\^'
export DISPLAY=:99

if ! pgrep -x Xvfb >/dev/null 2>&1; then
  echo "[xvfb] :99 기동"
  nohup Xvfb :99 -screen 0 1440x1000x24 -nolisten tcp >/tmp/xvfb_manus.log 2>&1 &
  sleep 3
fi
pgrep -x Xvfb >/dev/null 2>&1 || { echo "Xvfb 기동 실패"; exit 1; }

echo "######## Manus 에이전트 → $OUT ########"
$PY p1.py run --url "$URL" --proto manus --out "$OUT" 2>&1 | grep -vE "$F" | grep -E "liveness|관측 도구|\[run\] (P1 완료|⚠️)|bucket|memory_profile" | tail -7
$PY p2.py --profile "$OUT/p1/recovered_profile.yaml" --out "$OUT/p2" 2>&1 | grep -vE "$F" | grep "scope 분포"
$PY p3.py --profile "$OUT/p1/recovered_profile.yaml" --mapping "$OUT/p2/threat_mapping.yaml" --out "$OUT/p3" 2>&1 | grep -vE "$F" | grep "시나리오"
$PY p4.py --scenarios "$OUT/p3/scenarios.yaml" --url "$URL" --proto manus --out "$OUT/p4" 2>&1 | grep -vE "$F" | grep "trace →"
$PY p5.py --traces "$OUT/p4/traces.jsonl" --profile "$OUT/p1/recovered_profile.yaml" --out "$OUT/p5" 2>&1 | grep -vE "$F" | grep -E "돌파|baseline"
echo "######## Manus P1~P5 완료 → $OUT ########"
