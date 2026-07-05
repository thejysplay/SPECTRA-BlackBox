#!/bin/bash
# [P3-c] 적응형 다라운드 공격: p3(--prev로 직전 실패 반영)→p4→p5 를 돌파 또는 N라운드까지 반복.
# 단일 run 비결정성·근접실패를 흡수해 돌파율을 올린다.
# 사용: run_adaptive.sh <name> <url> [rounds]
PY=/home/kitesu/SPECTRA-BlackBox/Agent/damn-vulnerable-llm-agent/blackbox/bin/python
cd /home/kitesu/SPECTRA-BlackBox/Inspection
B=/home/kitesu/SPECTRA-BlackBox/Output
F='fastapi|litellm|proxy_server|cold_storage|Traceback|File "|ModuleNotFound|get_standard|clean_metadata|StandardLogging'
name=$1; url=$2; rounds=${3:-3}; O=$B/dvmn_$name
[ "$name" = DVLA ] && O=$B/dvla
prev=""; best=0
for r in $(seq 1 $rounds); do
  $PY p3.py --profile $O/p1/recovered_profile.yaml --mapping $O/p2/threat_mapping.yaml --out $O/p3 $prev >/dev/null 2>&1
  $PY p4.py --scenarios $O/p3/scenarios.yaml --url "$url" --out $O/p3 2>&1 | grep -qE "trace"
  br=$($PY p5.py --traces $O/p3/traces.jsonl --profile $O/p1/recovered_profile.yaml --out $O/p3 2>/dev/null | grep -oE "돌파 [0-9]+/[0-9]+" | tail -1)
  n=$(echo "$br" | grep -oE "[0-9]+" | head -1)
  echo "  [$name] round $r: $br"
  [ "${n:-0}" -gt "$best" ] && best=${n:-0}
  [ "${n:-0}" -gt 0 ] && { echo "  [$name] ✅ round $r 돌파 (적응 $r회)"; exit 0; }
  prev="--prev $O/p3/traces.jsonl"
done
echo "  [$name] ❌ $rounds라운드 미돌파 (best=$best)"
