#!/usr/bin/env bash
# KISA_C2LAB — AgentDojo 벤치 실행 래퍼 (gemini AI Studio, 2.5-flash).
# 사용:
#   ./run.sh -s workspace -ut user_task_0                     # 1개 태스크(utility)
#   ./run.sh -s workspace --attack important_instructions     # 기본 주입공격 ASR
#   ./run.sh -s workspace --attack spectra                    # 우리 공격(spectra)
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
: "${GEMINI_API_KEY:?set GEMINI_API_KEY env var first (export GEMINI_API_KEY=...)}"
export GOOGLE_API_KEY="$GEMINI_API_KEY"
# 모델: gemini-2.0-flash 폐기 상태 → 2.5-flash. (2.0 복귀 시 --model 로 교체)
exec "$HERE/.venv/bin/python" -m agentdojo.scripts.benchmark \
  --model GEMINI_2_5_FLASH --benchmark-version v1.1.2 "$@"
