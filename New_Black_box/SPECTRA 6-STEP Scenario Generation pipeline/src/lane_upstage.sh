#!/usr/bin/env bash
# Upstage 레인: solar-pro 계열은 API 키 1개 공유 → 반드시 순차(429 방지).
# solar-pro2 slack(잔여) → solar-pro3 3도메인 → solar-pro4 3도메인.
set -u
cd "/home/kitesu/SPECTRA-BlackBox/New_Black_box/SPECTRA 6-STEP Scenario Generation pipeline"
PY=/home/kitesu/SPECTRA-BlackBox/논문실험/agentdojo/repo/.venv/bin/python
declare -A TOT=([banking]=144 [travel]=141 [slack]=108)
PAIRS=(
  "solar-pro2 slack"
  "solar-pro3 banking" "solar-pro3 travel" "solar-pro3 slack"
  "solar-pro4 banking" "solar-pro4 travel" "solar-pro4 slack"
)
for pair in "${PAIRS[@]}"; do
  set -- $pair; M=$1; D=$2
  n=$(ls "data/asr_${D}__${M}"/*.json 2>/dev/null | grep -vc summary)
  if [ "$n" -ge "${TOT[$D]}" ]; then echo "[upstage skip] $M $D ($n/${TOT[$D]})"; continue; fi
  echo "===== [$(date +%H:%M)] UPSTAGE $M $D 시작 ($n/${TOT[$D]}) ====="
  $PY src/run_asr.py --domain "$D" --model "$M"
  echo "===== [$(date +%H:%M)] UPSTAGE $M $D 종료 exit=$? ====="
done
echo "@@@ Upstage 레인 종료 @@@"
