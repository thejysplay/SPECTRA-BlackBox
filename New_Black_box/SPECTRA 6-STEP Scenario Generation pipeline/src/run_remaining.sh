#!/usr/bin/env bash
# 남은 (모델,도메인) 쌍을 순차 실행. run_asr.py는 파일 단위 skip이라 재개/중복 안전.
set -u
source "$(dirname "${BASH_SOURCE[0]}")/_lane_env.sh"

# 순서: 프로바이더별로 묶음(DeepSeek 먼저, 그다음 Solar 3종). 이미 도는 쌍은 skip 로직이 처리.
PAIRS=(
  "deepseek-v4-flash travel"
  "deepseek-v4-flash slack"
  "solar-pro2 slack"
  "solar-pro3 banking"
  "solar-pro3 travel"
  "solar-pro3 slack"
  "solar-pro4 banking"
  "solar-pro4 travel"
  "solar-pro4 slack"
)

for pair in "${PAIRS[@]}"; do
  set -- $pair; MODEL=$1; DOM=$2
  n=$(ls "data/asr_${DOM}__${MODEL}"/*.json 2>/dev/null | grep -vc summary)
  if [ "$n" -ge "${TOT[$DOM]}" ]; then
    echo "[skip] $MODEL $DOM 이미완료 ($n/${TOT[$DOM]})"; continue
  fi
  echo "===== [$(date +%H:%M)] $MODEL $DOM 시작 (현재 $n/${TOT[$DOM]}) ====="
  $PY src/run_asr.py --domain "$DOM" --model "$MODEL"
  echo "===== [$(date +%H:%M)] $MODEL $DOM 종료 exit=$? ====="
done
echo "@@@ run_remaining 전체 종료 @@@"
