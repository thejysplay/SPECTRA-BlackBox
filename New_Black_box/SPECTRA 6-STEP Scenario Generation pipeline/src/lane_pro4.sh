#!/usr/bin/env bash
# solar-pro4 전용 레인 (사용자 요청: pro3와 병렬). banking→travel→slack 순차.
set -u
cd "/home/kitesu/SPECTRA-BlackBox/New_Black_box/SPECTRA 6-STEP Scenario Generation pipeline"
PY=/home/kitesu/SPECTRA-BlackBox/논문실험/agentdojo/repo/.venv/bin/python
declare -A TOT=([banking]=144 [travel]=141 [slack]=108)
for D in banking travel slack; do
  M=solar-pro4
  n=$(ls "data/asr_${D}__${M}"/*.json 2>/dev/null | grep -vc summary)
  if [ "$n" -ge "${TOT[$D]}" ]; then echo "[pro4 skip] $D ($n/${TOT[$D]})"; continue; fi
  echo "===== [$(date +%H:%M)] PRO4 $D 시작 ($n/${TOT[$D]}) ====="
  $PY src/run_asr.py --domain "$D" --model "$M"
  echo "===== [$(date +%H:%M)] PRO4 $D 종료 exit=$? ====="
done
echo "@@@ PRO4 레인 종료 @@@"
