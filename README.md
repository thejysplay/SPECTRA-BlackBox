# SPECTRA-BlackBox

**블랙박스(소스 비접근) LLM 에이전트 사전점검 파이프라인.**

배포된 LLM 에이전트를 소스 코드 없이 어댑터로만 상호작용하며, 공격적으로 정찰·돌파해 취약점을 사전 점검한다. 화이트박스 SPECTRA-AP의 블랙박스 대칭 도구.

## 파이프라인 P1~P5

| 단계 | 역할 | 처리 |
|---|---|---|
| **P1** 정찰 | 어댑터로 대상 질의 → Agent Spec 복원 | 고정질문 → LLM 심화질문(대상 맞춤) → 종합 |
| **P2** 스코핑 | Agent Spec × 위협카탈로그 매핑 | OWASP LLM Top10 36 + MITRE ATLAS 8 → 적용 / N_A / 관측불가 / 대리 |
| **P3** 시나리오 | 적용 위협 → 멀티턴 공격 생성 | setup → trigger |
| **P4** 실행·수집 | 어댑터로 대상 실행 | traces 수집 |
| **P5** 판정 | 공격 성공 자동 채점 | exploit_result |

- **어댑터 추상화**: `make_adapter(url)`이 URL만으로 Streamlit(T1, 도구단계)/API(T0, 텍스트) 자동 선택 → P 코드 무수정으로 다환경 점검
- **liveness 게이트**: 서로 다른 질문에 응답이 거의 동일하면(LLM 미연결 stub) 자동 식별해 정밀 점검 생략
- **2층 분리**: 인스펙터(블랙박스 공격수) / 평가자(정답 보유 채점, `score_gt.py`)

## 아키텍처 다이어그램

![전체 파이프라인 흐름도](assets/diagram1.png)

각 단계(P1~P5)·어댑터의 상세 아키텍처는 **[DIAGRAMS.md](DIAGRAMS.md)** 참고.

## 구조

```
Inspection/            점검 코드
  adapter.py           전송 추상화 (Streamlit/API)
  p1.py ~ p5.py        파이프라인 단계
  probe_catalog.yaml   정찰 질문지 (R1 고정 / R2 LLM 생성)
  threats/             OWASP + MITRE ATLAS 위협 spec
  score_gt.py          ground truth 채점
  run_fleet.sh         fleet 일괄 실행
Output/                대상별 산출물 + REPORT.md (시험 결과 보고서)
```

## 실행

```bash
# 단일 대상 P1~P5
python p1.py run --url <URL> --out Output/<대상>
python p2.py --profile Output/<대상>/p1/recovered_profile.yaml --out Output/<대상>/p2
python p3.py --profile ... --mapping Output/<대상>/p2/threat_mapping.yaml --out Output/<대상>/p3
python p4.py --scenarios Output/<대상>/p3/scenarios.yaml --url <URL> --out Output/<대상>/p3
python p5.py --traces Output/<대상>/p3/traces.jsonl --profile ... --out Output/<대상>/p3

# fleet 일괄
bash Inspection/run_fleet.sh
```

> P2/P3은 시나리오 생성에 LLM(Gemini)을 사용한다. `GEMINI_API_KEY`를 환경변수로 제공해야 한다(본 레포에 키 미포함).

## 점검 대상 (외부 레포 — 별도 clone)

본 레포는 점검 **도구**만 포함한다. 점검 대상은 외부 의도적 취약 에이전트로, 직접 clone해 구동한다:

- **DVLA** — Damn Vulnerable LLM Agent (ReversecLabs), streamlit / T1
- **DVMN** — damn-vulnerable-ai-agent (opena2a-org), OpenAI 호환 API / T0

(대상 레포 및 그 `.env` API key는 본 레포에 미포함)

## 시험 결과

`Output/REPORT.md` — 2개 환경 13개 에이전트 실증 (PPT용 11슬라이드 + 부록).

- 공격 성공 **4/4** (비밀 보유 대상 전부 노출) · 강건 대상 **0** (오탐 없음)
- DVLA 방어 1줄 유무로 **0/8 ↔ 7/8** (특이도·민감도)
- liveness 게이트로 stub 6종 자동 차단 · 방어 계층 ↔ 돌파 정확 상관
