# SPECTRA-BlackBox

**블랙박스(소스 비접근) LLM 에이전트 사전점검 파이프라인.**

배포된 LLM 에이전트를 소스 없이 표면(대화/프로토콜)만으로 상호작용하며 **정찰 → 위협 매핑 → 도메인 맞춤 공격 생성 → 실행 → 판정**한다. 핵심은 고정 공격 리스트가 아니라 **먼저 대상을 복원하고 그 명세로 그 에이전트에만 맞는 공격을 합성**하는 것(정찰↔공격 결합).

## 파이프라인 P1~P5

| 단계 | 역할 | 처리 |
|---|---|---|
| **P1** 정찰 | 표면 질의 → `agent_spec/v3` 복원 | R1 고정질문 34 → R2 LLM 심화 → 종합 + `recon_pool`(유출 격리) + liveness 플래그 |
| **P2** 스코핑 | agent_spec × 위협카탈로그 | **OWASP Agentic 15위협/59서브 + MITRE ATLAS 8케이스** → applicable/N_A/unobservable/proxy (facet 우선) |
| **P3** 생성 | applicable 위협 → 맞춤 공격 | 대상 도구·어휘·제약으로 발화 합성 (정찰↔공격 결합점) |
| **P4** 실행 | 대상 실행·관측 | traces 수집 |
| **P5** 판정 | 도메인 무관 4축 채점 | injection·scope·leakage·tool_exploit → exploit_result |

- **다중 표면**: chat · Streamlit · MCP · A2A · **IPI(간접 인젝션)** 를 단일 파이프라인으로. 어댑터는 프로토콜을 맞추는 배관일 뿐 핵심 기여 아님.
- **liveness**: 응답 다양성으로 stub 식별 — 차단이 아니라 진단 플래그(stub도 진짜 표면으로 공격 강행).
- **2층 분리**: 인스펙터(블랙박스 공격수) / 평가자(정답 보유 채점 `score_gt.py`).

## 실측 결과 (20 에이전트)

- **돌파 14 · AIM 방어 3 · 미돌파 3.** 정답(GT) 대비 판정 일치도 **90%(18/20)**.
- **ASR by surface**: MCP 100% · A2A 100% · IPI 50% · chat ~24% · streamlit 4% — 구조적 표면일수록 결정적.
- 논문용 도표 10종: `Output/PPT_자료/figures/` (PNG 300dpi + PDF).

## 구조

```
Inspection/
  p1.py ~ p5.py        파이프라인 단계
  adapter.py           전송 배관 / recon_multiproto.py (MCP·A2A) / attack_ipi.py (IPI)
  probe_catalog.yaml   정찰 질문지 (R1 고정 / R2 LLM 생성)
  gt_labels.yaml       정답 라벨 (20 에이전트)
  threats/             OWASP Agentic(T1–T15, 59 sub) + MITRE ATLAS(8 case)
  run_fleet.sh / run_adaptive.sh
Output/                대상별 산출물 + PPT_자료/figures (논문 도표)
```

자세한 방법론·결과·발견은 **[RESEARCH_README.md](RESEARCH_README.md)**, 단계별 다이어그램은 **[DIAGRAMS.md](DIAGRAMS.md)** 참고.

## 실행

```bash
# 단일 대상 P1~P5
python Inspection/p1.py run --url <URL> --out Output/<대상>
python Inspection/p2.py --profile Output/<대상>/p1/recovered_profile.yaml --out Output/<대상>/p2
python Inspection/p3.py --profile ... --mapping Output/<대상>/p2/threat_mapping.yaml --out Output/<대상>/p3
python Inspection/p4.py --scenarios Output/<대상>/p3/scenarios.yaml --url <URL> --out Output/<대상>/p3
python Inspection/p5.py --traces Output/<대상>/p3/traces.jsonl --profile ... --out Output/<대상>/p3

# fleet 일괄
bash Inspection/run_fleet.sh
```

> P1(R2)·P2·P3은 LLM(Gemini)을 사용 — `GEMINI_API_KEY` 필요(본 레포에 키 미포함).

## 점검 대상 (외부 레포 — 별도 clone)

본 레포는 점검 **도구**만 포함한다. 대상은 외부 의도적 취약 에이전트:

- **DVLA** — Damn Vulnerable LLM Agent, streamlit
- **DVAA** — damn-vulnerable-ai-agent, OpenAI 호환 API + MCP + A2A (19 에이전트)

모든 비밀은 교육용 테스트 더미(`dvaa-` 접두)·CTF 플래그. 로컬·권한 보유 하 방어적 사전점검 목적.
