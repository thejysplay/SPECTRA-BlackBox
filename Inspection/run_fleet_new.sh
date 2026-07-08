#!/bin/bash
# v8 파이프라인 fleet 일괄 P1~P5 → Output/new/<agent>/  (구 Output/dvmn_* 와 비교용)
# 로스터: DVMN 12 (OpenAI 호환 /v1/chat/completions) + DVLA (streamlit :5501)
PY=/home/kitesu/SPECTRA-BlackBox/Agent/damn-vulnerable-llm-agent/blackbox/bin/python
cd /home/kitesu/SPECTRA-BlackBox/Inspection
B=/home/kitesu/SPECTRA-BlackBox/Output/new
F='fastapi|litellm_logging|proxy_server|cold_storage|Traceback|File "|raise ImportError|ModuleNotFound|During handling|^[[:space:]]*\^|get_standard|clean_metadata|configured_cold|StandardLogging'

for entry in DVLA:5501 SecureBot:7001 HelperBot:7002 LegacyBot:7003 CodeBot:7004 RAGBot:7005 VisionBot:7006 MemoryBot:7007 RAGBot-AIM:7014 ResearchBot:7015 ResearchBot-AIM:7016 FlightBot:7017 FlightBot-AIM:7018; do
  name=${entry%:*}; port=${entry#*:}
  if [ "$name" = "DVLA" ]; then URL=http://localhost:$port; else URL=http://localhost:$port/v1/chat/completions; fi
  OUT=$B/$name
  echo "######## $name :$port → $OUT ########"
  $PY p1.py run --url "$URL" --out "$OUT" 2>&1 | grep -vE "$F" | grep -E "liveness|관측 도구|\[run\] (P1 완료|⚠️)|bucket|memory_profile" | tail -7
  $PY p2.py --profile "$OUT/p1/recovered_profile.yaml" --out "$OUT/p2" 2>&1 | grep -vE "$F" | grep "scope 분포"
  $PY p3.py --profile "$OUT/p1/recovered_profile.yaml" --mapping "$OUT/p2/threat_mapping.yaml" --out "$OUT/p3" 2>&1 | grep -vE "$F" | grep "시나리오"
  $PY p4.py --scenarios "$OUT/p3/scenarios.yaml" --url "$URL" --out "$OUT/p4" 2>&1 | grep -vE "$F" | grep "trace →"
  $PY p5.py --traces "$OUT/p4/traces.jsonl" --profile "$OUT/p1/recovered_profile.yaml" --out "$OUT/p5" 2>&1 | grep -vE "$F" | grep -E "돌파|baseline"
done
echo "######## FLEET(new/v8) 완료 ########"
