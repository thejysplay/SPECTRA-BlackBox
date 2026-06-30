#!/bin/bash
# DVMN fleet 일괄 P1~P5 (각 에이전트별 전체 파이프라인)
PY=/home/kitesu/SPECTRA-BlackBox/Agent/damn-vulnerable-llm-agent/blackbox/bin/python
cd /home/kitesu/SPECTRA-BlackBox/Inspection
B=/home/kitesu/SPECTRA-BlackBox/Output
F='fastapi|litellm_logging|proxy_server|cold_storage|Traceback|File "|raise ImportError|ModuleNotFound|During handling|^[[:space:]]*\^|get_standard|clean_metadata|configured_cold|StandardLogging'

for entry in SecureBot:7001 HelperBot:7002 LegacyBot:7003 CodeBot:7004 RAGBot:7005 VisionBot:7006 MemoryBot:7007 RAGBot-AIM:7014 ResearchBot:7015 ResearchBot-AIM:7016 FlightBot:7017 FlightBot-AIM:7018; do
  name=${entry%:*}; port=${entry#*:}
  URL=http://localhost:$port/v1/chat/completions
  OUT=$B/dvmn_$name
  echo "######## $name :$port ########"
  P1=$($PY p1.py run --url "$URL" --out "$OUT" 2>&1 | grep -vE "$F")
  echo "$P1" | grep -E "memory_profile|bucket (validated|recon)|liveness|관측 도구|\[run\] (P1 완료|⚠️)" | tail -7
  if echo "$P1" | grep -qE "liveness=(stub|no_response)"; then
    echo "  → ⚠️ stub/non-LLM(LLM 미연결) 감지 — P2~P5 생략(점검 유효성 게이트)"; continue
  fi
  $PY p2.py --profile "$OUT/p1/recovered_profile.yaml" --out "$OUT/p2" 2>&1 | grep -vE "$F" | grep "scope 분포"
  $PY p3.py --profile "$OUT/p1/recovered_profile.yaml" --mapping "$OUT/p2/threat_mapping.yaml" --out "$OUT/p3" 2>&1 | grep -vE "$F" | grep "시나리오"
  $PY p4.py --scenarios "$OUT/p3/scenarios.yaml" --url "$URL" --out "$OUT/p3" 2>&1 | grep -vE "$F" | grep "trace →"
  $PY p5.py --traces "$OUT/p3/traces.jsonl" --profile "$OUT/p1/recovered_profile.yaml" --out "$OUT/p3" 2>&1 | grep -vE "$F" | grep "돌파"
done
echo "######## FLEET 완료 ########"
