# STEP 2 — 인접 그래프 (v7)

2-gram 엣지 48개로 만든 인접 리스트. 노드 22개 · DAG 아님(사이클 19).

## 인접 리스트 (각 노드 → 올 수 있는 다음 노드)
각 줄의 **왼쪽 노드**가 곧 시작 후보(rule 이전엔 전부 시작 가능).

- **DAC-CS(자격증명·비밀)** → DAC-SRD(시스템·런타임 데이터), EXE-SSE(Shell·명령 실행), ID-RG(결과 생성)
- **DAC-SRD(시스템·런타임 데이터)** → INV-AT(응용 도구 호출)
- **DAC-UBD(사용자·업무 데이터)** → ID-ER(외부 공개), INV-AT(응용 도구 호출)
- **ENT-DI(직접입력)** → INV-AT(응용 도구 호출), INV-SCU(시스템·컴퓨터 조작)
- **ENT-II(간접입력)** → DAC-CS(자격증명·비밀), DAC-UBD(사용자·업무 데이터), HD-UI(사용자 유도), ID-RG(결과 생성), INV-AT(응용 도구 호출), INV-SCU(시스템·컴퓨터 조작), PST-CFG(지속 설정·규칙 잔류), PST-KB(지식베이스 잔류), PST-MEM(세션·메모리 잔류)
- **EXE-SE(코드·스크립트 실행)** → DAC-CS(자격증명·비밀)
- **EXE-SSE(Shell·명령 실행)** → ID-ER(외부 공개), PST-CFG(지속 설정·규칙 잔류), SC-DAT(데이터·파일 상태변경)
- **HD-UAD(사용자 승인·판단)** → EXE-SSE(Shell·명령 실행)
- **HD-UI(사용자 유도)** → HD-UI(사용자 유도), ID-ER(외부 공개)
- **ID-RG(결과 생성)** → HD-UI(사용자 유도), ID-ER(외부 공개)
- **INT-CR(설정·규칙 편입)** → PST-CFG(지속 설정·규칙 잔류)
- **INT-EC(실행형 편입)** → ENT-DI(직접입력), INV-AT(응용 도구 호출), PST-CFG(지속 설정·규칙 잔류)
- **INV-AT(응용 도구 호출)** → DAC-UBD(사용자·업무 데이터), EXE-SE(코드·스크립트 실행), EXE-SSE(Shell·명령 실행), HD-UAD(사용자 승인·판단), ID-ER(외부 공개), INV-SCU(시스템·컴퓨터 조작), PA-GA(부여 권한)
- **INV-SCU(시스템·컴퓨터 조작)** → DAC-CS(자격증명·비밀), EXE-SE(코드·스크립트 실행), EXE-SSE(Shell·명령 실행), ID-ER(외부 공개)
- **PA-GA(부여 권한)** → DAC-UBD(사용자·업무 데이터), SC-BIZ(업무·거래 상태변경), SC-SYS(시스템·설정 상태변경)
- **PST-CFG(지속 설정·규칙 잔류)** → ENT-II(간접입력), INV-AT(응용 도구 호출)
- **PST-KB(지식베이스 잔류)** → ENT-II(간접입력)
- **PST-MEM(세션·메모리 잔류)** → ENT-II(간접입력)

## 시작 후보 (source, out-edge 보유) — 18개
rule로 안 막으면 이 전부가 시작이 될 수 있음.

- DAC-CS(자격증명·비밀)
- DAC-SRD(시스템·런타임 데이터)
- DAC-UBD(사용자·업무 데이터)
- ENT-DI(직접입력)
- ENT-II(간접입력)
- EXE-SE(코드·스크립트 실행)
- EXE-SSE(Shell·명령 실행)
- HD-UAD(사용자 승인·판단)
- HD-UI(사용자 유도)
- ID-RG(결과 생성)
- INT-CR(설정·규칙 편입)
- INT-EC(실행형 편입)
- INV-AT(응용 도구 호출)
- INV-SCU(시스템·컴퓨터 조작)
- PA-GA(부여 권한)
- PST-CFG(지속 설정·규칙 잔류)
- PST-KB(지식베이스 잔류)
- PST-MEM(세션·메모리 잔류)

## sink (막다른 노드, out-edge 없음) — 4개

- ID-ER(외부 공개)
- SC-BIZ(업무·거래 상태변경)
- SC-DAT(데이터·파일 상태변경)
- SC-SYS(시스템·설정 상태변경)

## self-loop / 2-cycle (사이클 구조)

- self: HD-UI(사용자 유도)

- cycle: DAC-UBD(사용자·업무 데이터) ⇄ INV-AT(응용 도구 호출) · 근거 CS0037, CS0038, CS0039, CS0066
- cycle: ENT-II(간접입력) ⇄ PST-CFG(지속 설정·규칙 잔류) · 근거 CS0038, CS0041, CS0051
- cycle: ENT-II(간접입력) ⇄ PST-KB(지식베이스 잔류) · 근거 CS0024, CS0026, CS0035, CS0059
- cycle: ENT-II(간접입력) ⇄ PST-MEM(세션·메모리 잔류) · 근거 CS0040, CS0063, CS0066

---
참고: 실제 26 사건에서 관측된 첫 노드 4개·끝 노드 10개는 '사실'일 뿐 시작/종점 제한이 아님(제한은 STEP 4 rule).