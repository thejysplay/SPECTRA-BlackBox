# SPECTRA-BlackBox 아키텍처 다이어그램

> 실제 코드 구조(`p1~p5.py` · `adapter.py` · `score_gt.py`)를 반영. 편집용 Mermaid 소스는 `assets/diagramN.mmd`, 벡터 원본은 `assets/diagramN.svg`.

---

## 1. 전체 파이프라인 흐름도

블랙박스 대상에 어댑터로만 접근해 **정찰 → 스코핑 → 시나리오 → 실행 → 판정**으로 이어진다. 각 단계는 다음 단계의 입력이 되는 산출물을 남긴다.

![전체 파이프라인 흐름도](assets/diagram1.png)

---

## 2. P1 · 정찰 (Reconnaissance)

고정질문(R1) → 복원 → **liveness 게이트** → LLM 심화질문(R2) → 최종 Agent Spec. stub(LLM 미연결) 대상은 게이트에서 조기 종료된다.

![P1 정찰](assets/diagram2.png)

---

## 3. P2 · 스코핑 (Threat Scoping)

Agent Spec × 위협 카탈로그(OWASP LLM Top10 36 + MITRE ATLAS 8) → scope 4상태. 카탈로그는 그대로 끌어오고 scope·근거만 LLM이 생성(환각 방지).

![P2 스코핑](assets/diagram3.png)

---

## 4. P3 · 시나리오 생성 (Scenario)

applicable 위협 + recon_pool leakage + memory facet을 묶어 멀티턴 공격(setup→trigger)을 LLM으로 생성. 표준 injection 페이로드 + 비밀 값 추출을 노린다.

![P3 시나리오 생성](assets/diagram4.png)

---

## 5. P4 · 실행·수집 (Execution)

생성된 시나리오를 어댑터로 멀티턴 실행하고 응답을 trace로 수집. P1과 동일한 어댑터 메커니즘 재사용.

![P4 실행·수집](assets/diagram5.png)

---

## 6. P5 · 판정 + Ground Truth 채점 (2층)

P5는 trace를 자동 채점(scope_breach·injection·leakage)한다. 정규식 한계로 false negative가 있어, 평가자(정답 보유)가 `score_gt.py`로 실제 비밀 노출을 직접 채점한다 — 인스펙터/평가자 2층 분리.

![P5 판정 + ground truth 채점](assets/diagram6.png)

---

## 7. 어댑터 추상화 (다환경 범용성)

URL만으로 전송 계층을 자동 선택해 P 코드를 바꾸지 않고 여러 환경을 점검한다.

![어댑터 추상화](assets/diagram7.png)
