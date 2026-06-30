# SPECTRA-BlackBox 아키텍처 다이어그램

> GitHub는 Mermaid 코드블록을 자동 렌더링한다. 각 다이어그램은 실제 코드 구조(`p1~p5.py`, `adapter.py`, `score_gt.py`)를 반영한다.

---

## 1. 전체 파이프라인 흐름도

블랙박스 대상에 어댑터로만 접근해 정찰 → 스코핑 → 시나리오 → 실행 → 판정으로 이어진다. 각 단계는 다음 단계의 입력이 되는 산출물을 남긴다.

```mermaid
flowchart TD
    target(["대상 LLM 에이전트"])
    adapter["make_adapter(url)"]
    adapter -->|"Streamlit T1 / API T0"| target

    P1["P1 · 정찰"]
    P2["P2 · 스코핑"]
    P3["P3 · 시나리오 생성"]
    P4["P4 · 실행·수집"]
    P5["P5 · 판정"]
    GT["score_gt.py · ground truth 채점"]

    P1 --> RP["recovered_profile.yaml (Agent Spec)"]
    RP --> P2 --> TM["threat_mapping.yaml"]
    TM --> P3 --> SC["scenarios.yaml"]
    SC --> P4 --> TR["traces.jsonl"]
    TR --> P5 --> ER["exploit_result.yaml"]
    ER --> GT
    TR --> GT

    P1 -.->|"질의"| adapter
    P4 -.->|"공격 실행"| adapter
```

---

## 2. P1 · 정찰 (Reconnaissance)

고정질문(R1) → 복원 → liveness 게이트 → LLM 심화질문(R2) → 최종 Agent Spec. stub(LLM 미연결) 대상은 게이트에서 조기 종료된다.

```mermaid
flowchart TD
    cat["probe_catalog.yaml"]
    cat -->|"R1 고정질문"| col1["collect 수집"]
    col1 --> cls1["classify 복원"]
    cls1 --> lv{"liveness 게이트<br/>응답 다양성 낮으면 stub"}
    lv -->|"stub"| stop["조기 종료 · P2~P5 생략"]
    lv -->|"live"| gen["generate_r2 · Gemini 심화질문"]
    gen --> col2["collect R2 수집"]
    col2 --> cls2["classify 최종"]
    cls2 --> spec["Agent Spec<br/>identity · capability · boundary<br/>memory · injection · recon_pool"]
```

---

## 3. P2 · 스코핑 (Threat Scoping)

복원한 Agent Spec을 위협 카탈로그(OWASP+MITRE)와 LLM으로 매핑해 각 위협을 4상태로 분류한다. 카탈로그는 그대로 끌어오고 scope·근거만 LLM이 생성(환각 방지).

```mermaid
flowchart LR
    spec["Agent Spec"]
    cat["위협 카탈로그<br/>OWASP LLM Top10 36 + MITRE ATLAS 8"]
    spec --> map["LLM 매핑 · Gemini"]
    cat --> map
    map --> out["threat_mapping.yaml<br/>applicable / N_A / unobservable / proxy"]
```

---

## 4. P3 · 시나리오 생성 (Scenario)

적용(applicable) 위협 + 정찰에서 캐낸 leakage + memory facet을 묶어 멀티턴 공격(setup→trigger)을 LLM으로 생성한다. 표준 injection 페이로드 + 비밀 값 추출을 노린다.

```mermaid
flowchart LR
    a["applicable 위협"]
    l["recon_pool leakage"]
    m["memory stm/ltm"]
    a --> gen["LLM 시나리오 생성<br/>Gemini · 멀티턴"]
    l --> gen
    m --> gen
    gen --> sc["scenarios.yaml<br/>setup 에서 trigger 로"]
```

---

## 5. P4 · 실행·수집 (Execution)

생성된 시나리오를 어댑터로 대상에 멀티턴 실행하고 응답을 trace로 수집한다. P1과 동일한 어댑터 메커니즘을 재사용한다.

```mermaid
flowchart LR
    sc["scenarios.yaml"] --> ex["execute · 멀티턴 실행"]
    ex --> adapter["adapter"]
    adapter --> target(["대상 LLM 에이전트"])
    ex --> tr["traces.jsonl"]
```

---

## 6. P5 · 판정 + Ground Truth 채점 (2층)

P5는 trace를 자동 채점(scope_breach·injection·leakage)한다. 단 정규식 한계로 false negative가 있어, 평가자(정답 보유)가 `score_gt.py`로 실제 비밀 노출을 직접 채점한다 — 인스펙터/평가자 2층 분리.

```mermaid
flowchart TD
    subgraph inspector["인스펙터 · 블랙박스 (정답 모름)"]
        tr["traces.jsonl"] --> j["judge_one 자동판정"]
        base["arg_baseline (P1 관측 인자범위)"] --> j
        j --> er["exploit_result.yaml<br/>scope_breach · injection · leakage"]
    end

    subgraph evaluator["평가자 · 정답 보유 (채점)"]
        gtsrc["prompts.js 박힌 비밀 (ground truth)"] --> score["score_gt.py"]
        score --> result["공격 성공 4/4<br/>비밀 실제 노출 여부"]
    end

    er -.->|"false negative 보완"| score
```

---

## 7. 어댑터 추상화 (다환경 범용성)

URL만으로 전송 계층을 자동 선택해 P 코드를 바꾸지 않고 여러 환경을 점검한다.

```mermaid
flowchart TD
    url(["대상 URL"]) --> mk["make_adapter(url)"]
    mk -->|"chat/completions 포함"| api["APIAdapter<br/>OpenAI 호환 · T0 텍스트"]
    mk -->|"그 외"| st["StreamlitAdapter<br/>Playwright · T1 도구단계"]
    api --> obs["RawObservation<br/>visible_text · steps · tier"]
    st --> obs
    obs --> P["P1 / P4 공용 수집"]
```
