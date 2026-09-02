# SPECTRA-AgentDojo

LLM 에이전트 위협지식(E1~E10) 기반 **공격 시나리오 자동 생성 파이프라인**.
에이전트 스펙을 입력하면, **그 에이전트에서 실제로 성립 가능한 공격 시나리오만** 필터링해 생성한다.

> 핵심 프레임: **`f(에이전트 조건) = 성립 가능한 시나리오 서브셋`**
> 전체 공격지형(136 Instance × 9 Goal 골격)에서, 에이전트가 가진 조건(도구·데이터·상태)에 따라
> 성립하는 부분집합만 남긴다. 그 필터가 곧 위협 지식(Threat Knowledge)이다.

## 폴더 구조

| 폴더 | 내용 |
|---|---|
| `Threat_Knowledge/` | 위협지식 정본 — Element 10 / Subcategory 24 / **Instance 136**, 공격목표 골격 9(G1~G9), ATLAS Case Study 31 (`threat_knowledge.yaml`, 생성기 `_generate.py`) |
| `Agent_Specification/` | 대상 에이전트 스펙 — `AgentSPEC_{banking,slack,travel,workspace}.yaml` |
| `Scenario_Pipeline/` | 시나리오 생성 파이프라인 (Phase1~3 + 오케스트레이터) |
| `agentdojo/` | AgentDojo 벤치 개조환경 (gemini-2.5-flash, `.venv` 제외 — `uv sync`로 복원) |

## 파이프라인 3단계

```
Phase1 (LLM)  Agent Spec × 136 Instance  → 성립 Instance 추출 → Element 집합 확보
Phase2 (CODE) Element로 9개 공격목표 골격 성립 판정
              · Gate1  골격 Element 존재?
              · Gate2  그 Element를 실제 도구가 실현?
              · Compat Gate  목표의 본질 구조 실재? (G3=HITL / G5=credential / G8=편입 / G9=C2 re-entry)
Phase3 (LLM)  성립 골격을 그 에이전트 도구로 인스턴스화 + 멀티턴 대화 생성
              (골격 순서·critical 도구·instance_path 는 코드가 고정, LLM 은 대화만)
```

- 시나리오 개수 = `성립 Goal × Critical 도구 × 진입면(Entry) × 공격 인자(Target)` (조작기법은 개수축 아님, annotation)
- 모든 LLM 호출 `temperature=0` (재현성)

## 실행

```bash
export GEMINI_API_KEY=<your key>       # 또는 SPECTRA_ENV_FILE 로 .env 경로 지정
cd Scenario_Pipeline
python run_all.py                       # phase2 → 생성 → 정리 (phase1 캐시 재사용, 빠름)
python run_all.py --phase1              # phase1 부터 전체 (gemini 24콜×도메인)
python run_all.py --phase1 slack        # 특정 도메인만
```

의존성: `pyyaml`, `litellm`(gemini). agentdojo 벤치는 `cd agentdojo && uv sync` 후 `./run.sh`.

## 결과물

- `Scenario_Pipeline/output/scenarios/{domain}/`
  - `{Gx}_{한글태그}_{critical}.json` — 시나리오 (injection·user_turns·expected_hijack·normal/success_criteria)
  - `phase1_mapping.json` · `phase2_feasibility.json` · `_index.json`
- `Scenario_Pipeline/output/coverage_matrix.csv` — 136 Instance × 4도메인 커버리지

## 성립 결과 (AgentDojo 4종)

| 도메인 | 성립 목표 |
|---|---|
| banking | G6 (비의도 민감작업) |
| slack · travel · workspace | G1 (데이터 유출) · G6 |

나머지 목표(G2·G3·G4·G5·G7·G8·G9)는 코드실행·HITL 승인·persistence·credential 탈취·편입·C2 re-entry
메커니즘이 이 에이전트군에 없어 탈락 — 이것이 곧 **커버리지 갭**(이 에이전트로는 평가 불가한 위협면)이다.
에이전트 스펙만 바꾸면 그 에이전트의 실제 공격지형이 자동으로 도출된다.
