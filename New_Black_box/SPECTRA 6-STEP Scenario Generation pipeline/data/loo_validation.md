# LOO 일반화 검증 — 그래프가 미관측 사건을 예측하는가

케이스 하나를 빼고 나머지 25건으로 엣지를 재구축한 뒤, **빠진 케이스의 실제 관측 경로가 그 엣지들만으로 구성되는지** 본다. 구성되면 그 사건을 못 봤어도 생성 가능했다는 뜻.
LLM·환경 불필요(순수 조합) → 우리 벤치마크를 거치지 않는 외적 타당도 증거.

## 결과

- 케이스 **26** · 경로(flow) **33** · 엣지 **48**
- **완전 재현(exact): 15/33 = 45.5%**
- **1엣지 이내(within-1): 24/33 = 72.7%**
- 단일 케이스만 뒷받침하는 엣지: **26/48** — 이 엣지들이 LOO 실패의 직접 원인이다.

소실 엣지 수 분포: `0개` 15 flow · `1개` 9 flow · `2개` 7 flow · `4개` 2 flow

## 케이스별

| 케이스 | 분기 | 경로 | 엣지 | 소실 | 판정 |
|---|---|---|---|---|---|
| CS0021 | - | `ENT-II→ID-RG→ID-ER` | 2 | 0 | ✅ exact |
| CS0024 | - | `ENT-II→PST-KB→ENT-II→ID-RG→ID-ER` | 4 | 0 | ✅ exact |
| CS0026 | - | `ENT-II→PST-KB→ENT-II→ID-RG` | 3 | 0 | ✅ exact |
| CS0029 | - | `ENT-II→ID-RG→ID-ER` | 2 | 0 | ✅ exact |
| CS0037 | - | `ENT-II→INV-AT→DAC-UBD→INV-AT→DAC-UBD→INV-AT→ID-ER` | 6 | 0 | ✅ exact |
| CS0039 | - | `ENT-II→INV-AT→PA-GA→DAC-UBD→INV-AT→ID-ER` | 5 | 0 | ✅ exact |
| CS0040 | - | `ENT-II→PST-MEM` | 1 | 0 | ✅ exact |
| CS0046 | - | `ENT-II→INV-SCU→EXE-SSE→SC-DAT` | 3 | 0 | ✅ exact |
| CS0052 | - | `ENT-DI→INV-SCU→EXE-SE` | 2 | 0 | ✅ exact |
| CS0055 | - | `ENT-II→INV-SCU→EXE-SSE` | 2 | 0 | ✅ exact |
| CS0061 | - | `ENT-II→INV-AT→ID-ER` | 2 | 0 | ✅ exact |
| CS0066 | 유출 | `ENT-II→INV-AT→DAC-UBD→ID-ER` | 3 | 0 | ✅ exact |
| CS0066 | 지속 (메모리 변조) | `ENT-II→PST-MEM` | 1 | 0 | ✅ exact |
| CS0066 | 재배포 (측면 이동) | `ENT-II→INV-AT→DAC-UBD→INV-AT→ID-ER` | 4 | 0 | ✅ exact |
| CS0067 | - | `ENT-II→INV-SCU→DAC-CS→ID-RG` | 3 | 0 | ✅ exact |
| CS0016 | - | `ENT-DI→INV-SCU→EXE-SE→DAC-CS→ID-RG` | 4 | 1 | △ within-1 |
| CS0038 | - | `ENT-II→PST-CFG→ENT-II→INV-AT→DAC-UBD` | 4 | 1 | △ within-1 |
| CS0041 | - | `INT-CR→PST-CFG→ENT-II→ID-RG` | 3 | 1 | △ within-1 |
| CS0047 | - | `INT-EC→ENT-DI→INV-SCU→EXE-SSE→SC-DAT` | 4 | 1 | △ within-1 |
| CS0059 | - | `ENT-II→PST-KB→ENT-II→DAC-UBD→ID-ER` | 4 | 1 | △ within-1 |
| CS0063 | F 데이터 유출 | `ENT-II→PST-MEM→ENT-II→INV-AT→PA-GA→DAC-UBD→ID-ER` | 6 | 1 | △ within-1 |
| CS0063 | D 위치 추적 | `ENT-II→PST-MEM→ENT-II→INV-SCU→ID-ER` | 4 | 1 | △ within-1 |
| CS0063 | E 프라이버시 침해 | `ENT-II→PST-MEM→ENT-II→INV-SCU` | 3 | 1 | △ within-1 |
| CS0063 | A 무결성 침해 | `ENT-II→PST-MEM→ENT-II→ID-RG` | 3 | 1 | △ within-1 |
| CS0020 | - | `ENT-II→HD-UI→HD-UI→ID-ER` | 3 | 2 | ❌ |
| CS0035 | - | `ENT-II→PST-KB→ENT-II→DAC-CS→ID-RG→HD-UI→ID-ER` | 6 | 2 | ❌ |
| CS0045 | - | `ENT-II→INV-SCU→DAC-CS→EXE-SSE→ID-ER` | 4 | 2 | ❌ |
| CS0051 | - | `ENT-II→INV-AT→EXE-SSE→PST-CFG→ENT-II→INV-SCU→ID-ER` | 6 | 2 | ❌ |
| CS0062 | - | `ENT-DI→INV-AT→EXE-SE` | 2 | 2 | ❌ |
| CS0063 | B 데이터 파괴 | `ENT-II→PST-MEM→ENT-II→INV-AT→PA-GA→SC-BIZ` | 5 | 2 | ❌ |
| CS0063 | C 물리 제어 | `ENT-II→PST-MEM→ENT-II→INV-AT→PA-GA→SC-SYS` | 5 | 2 | ❌ |
| CS0049 | - | `INT-EC→PST-CFG→INV-AT→HD-UAD→EXE-SSE` | 4 | 4 | ❌ |
| CS0054 | - | `INT-EC→INV-AT→INV-SCU→DAC-CS→DAC-SRD→INV-AT→ID-ER` | 6 | 4 | ❌ |

## 가장 자주 소실된 전이

그 케이스에만 의존해 다른 사건으로부터는 복원되지 않는 전이 = 지식의 단일점.

| 전이 | 소실 flow 수 |
|---|---|
| `PST-MEM→ENT-II` | 6 |
| `EXE-SE→DAC-CS` | 1 |
| `ENT-II→HD-UI` | 1 |
| `HD-UI→HD-UI` | 1 |
| `ENT-II→DAC-CS` | 1 |
| `ID-RG→HD-UI` | 1 |
| `ENT-II→PST-CFG` | 1 |
| `INT-CR→PST-CFG` | 1 |
| `DAC-CS→EXE-SSE` | 1 |
| `EXE-SSE→ID-ER` | 1 |
| `INT-EC→ENT-DI` | 1 |
| `INT-EC→PST-CFG` | 1 |
| `PST-CFG→INV-AT` | 1 |
| `INV-AT→HD-UAD` | 1 |
| `HD-UAD→EXE-SSE` | 1 |