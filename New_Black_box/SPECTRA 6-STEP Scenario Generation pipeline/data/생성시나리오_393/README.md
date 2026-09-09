# 생성 시나리오 (SPECTRA, 워크스페이스 제외 3도메인)

AgentDojo 원본 개수(워크스페이스 제외 389)에 맞춰 생성한 점검 시나리오 **393건**.

| 도메인 | 건수 | 원본 AgentDojo | 목표 분포 |
|---|---|---|---|
| banking | 144 | 144 | DAC-UBD 48 · SC-BIZ 48 · SC-SYS 48 |
| travel | 141 | 140 | DAC-UBD 47 · ID-ER 47 · SC-BIZ 47 |
| slack | 108 | 105 | DAC-UBD 27 · ID-ER 27 · SC-BIZ 27 · SC-SYS 27 |
| **합** | **393** | **389** | |

## 생성 방식
- **지식DB(에이전트 무관)** STEP1~4 → 1,279 서브카테고리 시퀀스
- **에이전트 필터(STEP5)** + **도구 원자성 realizable** → ENT-II(간접주입)·read-first 정본 뼈대
- **인스턴스 조합 + 사회공학 6기법 로테이션** → 목표 균등 배분, temp=0 결정론
- **위협모델**: 간접 프롬프트 인젝션 (user_input 정상, payload가 채널에 삽입)

## 파일 필드 (각 .json)
| 필드 | 뜻 |
|---|---|
| `skeleton` | 서브카테고리 뼈대 (예: ENT-II→INV-AT→DAC-UBD→INV-AT→PA-GA→SC-BIZ) |
| `goal` / `goal_ko` | 공격 목표 서브카테고리 |
| `adv_technique` | 배정된 사회공학 기법 (권위위장·시간압박·포맷위장·정당업무위장·간접트리거·신뢰악용) |
| `instances` / `tools_used` | 위치별 인스턴스·도구 선택 |
| `provenance` | 전이 근거 CS(엣지) + 원본 CS 여부 |
| `generated.turns` | 유저입력(정상) + payload(주입문, 채널에 삽입) |
| `generated.expected_tool_calls` | 성공 시 기대 도구콜(오라클) |
| `generated.success_criteria` | ASR 판정 성공기준 |

## 타당성 (goal_ok = 마지막 도구콜이 목표 실현)
- banking 100% · travel 100% · slack 99% (원자성 수정 후 뼈대열정합 99~100%)

## ASR (개조 AgentDojo, gemini-2.5-flash, 우리 LLM judge)
- **banking 7.6%** (송금 0% · 계정변경 8% · 데이터접근 15%)
- travel · slack: 미측정
