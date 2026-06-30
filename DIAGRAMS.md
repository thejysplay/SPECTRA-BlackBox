# SPECTRA-BlackBox 아키텍처 다이어그램

각 단계의 그림 + 입력/처리/출력(I/O) 상세 설명. 실제 코드(`p1~p5.py` · `adapter.py` · `score_gt.py`)를 반영한다.
편집용 Mermaid 소스는 `assets/diagramN.mmd`, 벡터 원본은 `assets/diagramN.svg`.

전체 데이터 흐름: **대상 URL → (어댑터) → P1 정찰 → P2 스코핑 → P3 시나리오 → P4 실행 → P5 판정 → ground truth 채점**. 각 단계는 파일 산출물로 다음 단계에 넘긴다.

---

## 1. 전체 파이프라인 흐름도

블랙박스 대상에 어댑터로만 접근해 **정찰 → 스코핑 → 시나리오 → 실행 → 판정**으로 이어진다. 각 단계는 다음 단계의 입력이 되는 산출물을 남긴다.

![전체 파이프라인 흐름도](assets/diagram1.png)

**단계별 산출물 한눈에:**

| 단계 | 입력 | 출력 |
|---|---|---|
| P1 정찰 | 대상 URL + `probe_catalog.yaml` | `recovered_profile.yaml` (Agent Spec) |
| P2 스코핑 | recovered_profile + 위협카탈로그 | `threat_mapping.yaml` |
| P3 시나리오 | recovered_profile + threat_mapping | `scenarios.yaml` |
| P4 실행 | scenarios + 대상 URL | `traces.jsonl` |
| P5 판정 | traces + recovered_profile | `exploit_result.yaml` |
| 채점 | traces + 정답 비밀 | 공격 성공 N/M |

---

## 2. P1 · 정찰 (Reconnaissance) — `p1.py run`

![P1 정찰](assets/diagram2.png)

| | 내용 |
|---|---|
| **입력** | 대상 URL + `probe_catalog.yaml`(질문지 16 strand) |
| **출력** | `recovered_profile.yaml` (= Agent Spec) |

**내부 흐름 (5단계):**
1. **R1 수집** — 고정질문(정체성·능력·권한경계·게이트·인자주입·메모리·거부기준 등)을 어댑터로 대상에 질의 → `runs/r1.jsonl`
2. **R1 복원** — `classify()`가 응답을 분류(도구 카테고리·경계신호·leakage) → 1차 프로필
3. **liveness 게이트** — 서로 다른 질문에 응답이 거의 동일(distinct 비율 < 0.15)하면 **stub(LLM 미연결)으로 판정 → 조기 종료**(P2~P5 생략)
4. **R2 생성·수집** — Gemini가 R1 기반 **대상 맞춤 심화질문** 생성 → 어댑터 재질의 → `runs/r2.jsonl`
5. **최종 복원** — R1+R2 종합 → Agent Spec

**Agent Spec 구조(출력):** `identity`(자기보고) · `capability`(도구·인자범위) · `boundary`(거부지점·게이트) · `memory`(stm/ltm) · `injection_surface` · `observability`(tier·**liveness**) · `recon_pool`(짜낸 leakage = P3 재료) · `provenance`(원본 추적)

---

## 3. P2 · 스코핑 (Threat Scoping) — `p2.py`

![P2 스코핑](assets/diagram3.png)

| | 내용 |
|---|---|
| **입력** | `recovered_profile.yaml` + `threats/`(OWASP LLM Top10 36 sub + MITRE ATLAS 8 case) |
| **출력** | `threat_mapping.yaml` |

**처리:** Agent Spec × 각 위협 → Gemini가 **scope 4상태**(applicable / N_A / unobservable / proxy) + 근거 판정. 카탈로그는 **그대로 복사**하고 scope·이유만 LLM이 생성(환각 방지).
**예 (LegacyBot):** applicable 7 / N_A 38 / unobservable 1 → 적용 위협 7개만 P3로 전달

---

## 4. P3 · 시나리오 생성 (Scenario) — `p3.py`

![P3 시나리오 생성](assets/diagram4.png)

| | 내용 |
|---|---|
| **입력** | `recovered_profile.yaml` + `threat_mapping.yaml` |
| **출력** | `scenarios.yaml` |

**처리:** ① applicable 위협 + ② recon_pool의 leakage + ③ memory facet(stm/ltm)을 묶어 → Gemini가 **멀티턴 공격(setup→trigger)** 생성. 표준 injection 페이로드(한국어+영어) + 비밀 '값'까지 추출 지향.
**예 (LegacyBot):** 9개 시나리오 (T5-S1 · LEAK-exfil · MEM-poison 등)

---

## 5. P4 · 실행·수집 (Execution) — `p4.py`

![P4 실행·수집](assets/diagram5.png)

| | 내용 |
|---|---|
| **입력** | `scenarios.yaml` + 대상 URL |
| **출력** | `traces.jsonl` |

**처리:** `execute()`가 어댑터로 각 시나리오를 **멀티턴 실행**(시나리오 간 세션 reset), setup→trigger 응답을 trace로 기록. P1과 동일한 어댑터 메커니즘 재사용.

---

## 6. P5 · 판정 + Ground Truth 채점 (2층) — `p5.py` · `score_gt.py`

![P5 판정 + ground truth 채점](assets/diagram6.png)

**P5 자동판정 (인스펙터, 정답 모름):**
| | 내용 |
|---|---|
| **입력** | `traces.jsonl` + `recovered_profile`(arg_baseline) |
| **출력** | `exploit_result.yaml` |
| **처리** | trace마다 scope_breach(P1 인자범위 밖)·injection_reached·leakage(비밀 패턴) 자동 채점 |
| **한계** | 정규식이 실제 비밀 토큰(`dvaa-...`)을 일부 못 잡는 **false negative** |

**Ground Truth 채점 (평가자, 정답 보유):**
| | 내용 |
|---|---|
| **입력** | traces + runs + **prompts.js 박힌 실제 비밀**(정답) |
| **출력** | 공격 성공 N/M (실제 노출 여부) |
| **처리** | 대상의 진짜 비밀을 알고 실제 노출로 직접 채점 → P5 누락 보완 |

→ 인스펙터(자동)와 평가자(정답)를 분리해, 알려진 대상에서 방법론 자체를 자기검증한다.

---

## 7. 어댑터 추상화 (다환경 범용성) — `adapter.py`

![어댑터 추상화](assets/diagram7.png)

| | 내용 |
|---|---|
| **입력** | 대상 URL |
| **처리** | `make_adapter(url)` — `/chat/completions` 있으면 `APIAdapter`(OpenAI 호환, T0 텍스트), 아니면 `StreamlitAdapter`(Playwright, T1 도구단계) 자동 선택 |
| **출력** | `RawObservation`(visible_text · disclosed_steps · observation_tier) |
| **효과** | P 코드를 안 바꾸고 URL만으로 DVLA(T1)·DVMN(T0) 둘 다 점검 |

---

## 종합 결과 (3라운드 실증)

| 환경 | 대상 | 결과 |
|---|---|---|
| **DVMN** 유효 6 | LegacyBot · HelperBot · RAGBot · MemoryBot | 🔴 비밀 **4/4 전부 노출** (공격 성공) |
| | SecureBot(hardened) · CodeBot | ⚪ 0 (방어 / 비밀 없음) |
| **DVMN** stub 6 | Vision · Research · Flight · AIM 계열 | liveness 게이트 **자동 차단** |
| **DVLA** | 원본 / 약화 | 0/8 ↔ **7/8** (특이도 / 민감도) |

**핵심:** 동일 P1~P5로 두 환경(T1·T0)을 점검 → 비밀 보유 대상은 전부 돌파·강건 대상은 0. **방어 계층이 돌파를 가른다**(DVLA는 방어 1줄 유무로 0↔7). 상세 보고서는 [`Output/REPORT.md`](Output/REPORT.md).
