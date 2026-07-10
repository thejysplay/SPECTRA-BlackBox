#!/bin/bash
# Genspark 슈퍼에이전트 P1~P5 파이프라인 (v8). 결과: Output/new/Genspark/
# ⚠️ Genspark은 headless 차단 → Xvfb 가상화면에 headed로 실행(이 스크립트가 DISPLAY 세팅).
# 전제: .spectra_sessions/genspark 로그인 세션 존재(noVNC로 1회 로그인).
#       로그인 noVNC 스택이 떠 있으면 먼저: bash Inspection/novnc_down.sh .spectra_sessions/genspark
set -u
SB=/home/kitesu/SPECTRA-BlackBox
PY=$SB/Agent/damn-vulnerable-llm-agent/blackbox/bin/python
cd "$SB/Inspection"
URL="https://www.genspark.ai/"
OUT="$SB/Output/new/Genspark"
F='fastapi|litellm_logging|proxy_server|Traceback|File "|raise ImportError|ModuleNotFound|During handling|^[[:space:]]*\^'
export DISPLAY=:99

# Genspark은 headed 필수 → Xvfb :99 없으면 기동
if ! pgrep -x Xvfb >/dev/null 2>&1; then
  echo "[xvfb] :99 기동"
  nohup Xvfb :99 -screen 0 1440x1000x24 -nolisten tcp >/tmp/xvfb_genspark.log 2>&1 &
  sleep 3
fi
pgrep -x Xvfb >/dev/null 2>&1 || { echo "Xvfb 기동 실패"; exit 1; }

echo "######## Genspark 슈퍼에이전트 → $OUT ########"
$PY p1.py run --url "$URL" --proto genspark --out "$OUT" 2>&1 | grep -vE "$F" | grep -E "liveness|관측 도구|\[run\] (P1 완료|⚠️)|bucket|memory_profile" | tail -7
$PY p2.py --profile "$OUT/p1/recovered_profile.yaml" --out "$OUT/p2" 2>&1 | grep -vE "$F" | grep "scope 분포"
$PY p3.py --profile "$OUT/p1/recovered_profile.yaml" --mapping "$OUT/p2/threat_mapping.yaml" --out "$OUT/p3" 2>&1 | grep -vE "$F" | grep "시나리오"
$PY p4.py --scenarios "$OUT/p3/scenarios.yaml" --url "$URL" --proto genspark --out "$OUT/p4" 2>&1 | grep -vE "$F" | grep "trace →"
$PY p5.py --traces "$OUT/p4/traces.jsonl" --profile "$OUT/p1/recovered_profile.yaml" --out "$OUT/p5" 2>&1 | grep -vE "$F" | grep -E "돌파|baseline"
echo "######## Genspark P1~P5 완료 → $OUT ########"
