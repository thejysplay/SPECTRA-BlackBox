# STEP 3 — 경로(시나리오) 생성 (v7)

시작 정책=broad(18 노드) · 종점 도달 walk · 사이클 허용+반복상한 · 최대 7노드.
전체 **5068** = 관측재현 31 + 신규 5037. (참고: 시작을 관측 4개로 좁히면 1324개)

표기: `코드(한국어)`.

## 실제 관측된 공격 흐름 31개 (기본)

1. ENT-DI(직접입력) → INV-AT(응용 도구 호출) → EXE-SE(코드·스크립트 실행)
2. ENT-DI(직접입력) → INV-SCU(시스템·컴퓨터 조작) → EXE-SE(코드·스크립트 실행)
3. ENT-DI(직접입력) → INV-SCU(시스템·컴퓨터 조작) → EXE-SE(코드·스크립트 실행) → DAC-CS(자격증명·비밀) → ID-RG(결과 생성)
4. ENT-II(간접입력) → HD-UI(사용자 유도) → HD-UI(사용자 유도) → ID-ER(외부 공개)
5. ENT-II(간접입력) → ID-RG(결과 생성) → ID-ER(외부 공개)
6. ENT-II(간접입력) → INV-AT(응용 도구 호출) → DAC-UBD(사용자·업무 데이터) → ID-ER(외부 공개)
7. ENT-II(간접입력) → INV-AT(응용 도구 호출) → DAC-UBD(사용자·업무 데이터) → INV-AT(응용 도구 호출) → DAC-UBD(사용자·업무 데이터) → INV-AT(응용 도구 호출) → ID-ER(외부 공개)
8. ENT-II(간접입력) → INV-AT(응용 도구 호출) → DAC-UBD(사용자·업무 데이터) → INV-AT(응용 도구 호출) → ID-ER(외부 공개)
9. ENT-II(간접입력) → INV-AT(응용 도구 호출) → EXE-SSE(Shell·명령 실행) → PST-CFG(지속 설정·규칙 잔류) → ENT-II(간접입력) → INV-SCU(시스템·컴퓨터 조작) → ID-ER(외부 공개)
10. ENT-II(간접입력) → INV-AT(응용 도구 호출) → ID-ER(외부 공개)
11. ENT-II(간접입력) → INV-AT(응용 도구 호출) → PA-GA(부여 권한) → DAC-UBD(사용자·업무 데이터) → INV-AT(응용 도구 호출) → ID-ER(외부 공개)
12. ENT-II(간접입력) → INV-SCU(시스템·컴퓨터 조작) → DAC-CS(자격증명·비밀) → EXE-SSE(Shell·명령 실행) → ID-ER(외부 공개)
13. ENT-II(간접입력) → INV-SCU(시스템·컴퓨터 조작) → DAC-CS(자격증명·비밀) → ID-RG(결과 생성)
14. ENT-II(간접입력) → INV-SCU(시스템·컴퓨터 조작) → EXE-SSE(Shell·명령 실행)
15. ENT-II(간접입력) → INV-SCU(시스템·컴퓨터 조작) → EXE-SSE(Shell·명령 실행) → SC-DAT(데이터·파일 상태변경)
16. ENT-II(간접입력) → PST-CFG(지속 설정·규칙 잔류) → ENT-II(간접입력) → INV-AT(응용 도구 호출) → DAC-UBD(사용자·업무 데이터)
17. ENT-II(간접입력) → PST-KB(지식베이스 잔류) → ENT-II(간접입력) → DAC-CS(자격증명·비밀) → ID-RG(결과 생성) → HD-UI(사용자 유도) → ID-ER(외부 공개)
18. ENT-II(간접입력) → PST-KB(지식베이스 잔류) → ENT-II(간접입력) → DAC-UBD(사용자·업무 데이터) → ID-ER(외부 공개)
19. ENT-II(간접입력) → PST-KB(지식베이스 잔류) → ENT-II(간접입력) → ID-RG(결과 생성)
20. ENT-II(간접입력) → PST-KB(지식베이스 잔류) → ENT-II(간접입력) → ID-RG(결과 생성) → ID-ER(외부 공개)
21. ENT-II(간접입력) → PST-MEM(세션·메모리 잔류)
22. ENT-II(간접입력) → PST-MEM(세션·메모리 잔류) → ENT-II(간접입력) → ID-RG(결과 생성)
23. ENT-II(간접입력) → PST-MEM(세션·메모리 잔류) → ENT-II(간접입력) → INV-AT(응용 도구 호출) → PA-GA(부여 권한) → DAC-UBD(사용자·업무 데이터) → ID-ER(외부 공개)
24. ENT-II(간접입력) → PST-MEM(세션·메모리 잔류) → ENT-II(간접입력) → INV-AT(응용 도구 호출) → PA-GA(부여 권한) → SC-BIZ(업무·거래 상태변경)
25. ENT-II(간접입력) → PST-MEM(세션·메모리 잔류) → ENT-II(간접입력) → INV-AT(응용 도구 호출) → PA-GA(부여 권한) → SC-SYS(시스템·설정 상태변경)
26. ENT-II(간접입력) → PST-MEM(세션·메모리 잔류) → ENT-II(간접입력) → INV-SCU(시스템·컴퓨터 조작)
27. ENT-II(간접입력) → PST-MEM(세션·메모리 잔류) → ENT-II(간접입력) → INV-SCU(시스템·컴퓨터 조작) → ID-ER(외부 공개)
28. INT-CR(설정·규칙 편입) → PST-CFG(지속 설정·규칙 잔류) → ENT-II(간접입력) → ID-RG(결과 생성)
29. INT-EC(실행형 편입) → ENT-DI(직접입력) → INV-SCU(시스템·컴퓨터 조작) → EXE-SSE(Shell·명령 실행) → SC-DAT(데이터·파일 상태변경)
30. INT-EC(실행형 편입) → INV-AT(응용 도구 호출) → INV-SCU(시스템·컴퓨터 조작) → DAC-CS(자격증명·비밀) → DAC-SRD(시스템·런타임 데이터) → INV-AT(응용 도구 호출) → ID-ER(외부 공개)
31. INT-EC(실행형 편입) → PST-CFG(지속 설정·규칙 잔류) → INV-AT(응용 도구 호출) → HD-UAD(사용자 승인·판단) → EXE-SSE(Shell·명령 실행)

## 새로 조합된 시나리오 예시 20개 (신규)

1. DAC-CS(자격증명·비밀) → DAC-SRD(시스템·런타임 데이터)
2. DAC-CS(자격증명·비밀) → DAC-SRD(시스템·런타임 데이터) → INV-AT(응용 도구 호출)
3. DAC-CS(자격증명·비밀) → DAC-SRD(시스템·런타임 데이터) → INV-AT(응용 도구 호출) → DAC-UBD(사용자·업무 데이터)
4. DAC-CS(자격증명·비밀) → DAC-SRD(시스템·런타임 데이터) → INV-AT(응용 도구 호출) → DAC-UBD(사용자·업무 데이터) → ID-ER(외부 공개)
5. DAC-CS(자격증명·비밀) → DAC-SRD(시스템·런타임 데이터) → INV-AT(응용 도구 호출) → DAC-UBD(사용자·업무 데이터) → INV-AT(응용 도구 호출)
6. DAC-CS(자격증명·비밀) → DAC-SRD(시스템·런타임 데이터) → INV-AT(응용 도구 호출) → DAC-UBD(사용자·업무 데이터) → INV-AT(응용 도구 호출) → DAC-UBD(사용자·업무 데이터)
7. DAC-CS(자격증명·비밀) → DAC-SRD(시스템·런타임 데이터) → INV-AT(응용 도구 호출) → DAC-UBD(사용자·업무 데이터) → INV-AT(응용 도구 호출) → DAC-UBD(사용자·업무 데이터) → ID-ER(외부 공개)
8. DAC-CS(자격증명·비밀) → DAC-SRD(시스템·런타임 데이터) → INV-AT(응용 도구 호출) → DAC-UBD(사용자·업무 데이터) → INV-AT(응용 도구 호출) → DAC-UBD(사용자·업무 데이터) → INV-AT(응용 도구 호출)
9. DAC-CS(자격증명·비밀) → DAC-SRD(시스템·런타임 데이터) → INV-AT(응용 도구 호출) → DAC-UBD(사용자·업무 데이터) → INV-AT(응용 도구 호출) → EXE-SE(코드·스크립트 실행)
10. DAC-CS(자격증명·비밀) → DAC-SRD(시스템·런타임 데이터) → INV-AT(응용 도구 호출) → DAC-UBD(사용자·업무 데이터) → INV-AT(응용 도구 호출) → EXE-SSE(Shell·명령 실행)
11. DAC-CS(자격증명·비밀) → DAC-SRD(시스템·런타임 데이터) → INV-AT(응용 도구 호출) → DAC-UBD(사용자·업무 데이터) → INV-AT(응용 도구 호출) → EXE-SSE(Shell·명령 실행) → ID-ER(외부 공개)
12. DAC-CS(자격증명·비밀) → DAC-SRD(시스템·런타임 데이터) → INV-AT(응용 도구 호출) → DAC-UBD(사용자·업무 데이터) → INV-AT(응용 도구 호출) → EXE-SSE(Shell·명령 실행) → PST-CFG(지속 설정·규칙 잔류)
13. DAC-CS(자격증명·비밀) → DAC-SRD(시스템·런타임 데이터) → INV-AT(응용 도구 호출) → DAC-UBD(사용자·업무 데이터) → INV-AT(응용 도구 호출) → EXE-SSE(Shell·명령 실행) → SC-DAT(데이터·파일 상태변경)
14. DAC-CS(자격증명·비밀) → DAC-SRD(시스템·런타임 데이터) → INV-AT(응용 도구 호출) → DAC-UBD(사용자·업무 데이터) → INV-AT(응용 도구 호출) → HD-UAD(사용자 승인·판단)
15. DAC-CS(자격증명·비밀) → DAC-SRD(시스템·런타임 데이터) → INV-AT(응용 도구 호출) → DAC-UBD(사용자·업무 데이터) → INV-AT(응용 도구 호출) → HD-UAD(사용자 승인·판단) → EXE-SSE(Shell·명령 실행)
16. DAC-CS(자격증명·비밀) → DAC-SRD(시스템·런타임 데이터) → INV-AT(응용 도구 호출) → DAC-UBD(사용자·업무 데이터) → INV-AT(응용 도구 호출) → ID-ER(외부 공개)
17. DAC-CS(자격증명·비밀) → DAC-SRD(시스템·런타임 데이터) → INV-AT(응용 도구 호출) → DAC-UBD(사용자·업무 데이터) → INV-AT(응용 도구 호출) → INV-SCU(시스템·컴퓨터 조작)
18. DAC-CS(자격증명·비밀) → DAC-SRD(시스템·런타임 데이터) → INV-AT(응용 도구 호출) → DAC-UBD(사용자·업무 데이터) → INV-AT(응용 도구 호출) → INV-SCU(시스템·컴퓨터 조작) → EXE-SE(코드·스크립트 실행)
19. DAC-CS(자격증명·비밀) → DAC-SRD(시스템·런타임 데이터) → INV-AT(응용 도구 호출) → DAC-UBD(사용자·업무 데이터) → INV-AT(응용 도구 호출) → INV-SCU(시스템·컴퓨터 조작) → EXE-SSE(Shell·명령 실행)
20. DAC-CS(자격증명·비밀) → DAC-SRD(시스템·런타임 데이터) → INV-AT(응용 도구 호출) → DAC-UBD(사용자·업무 데이터) → INV-AT(응용 도구 호출) → INV-SCU(시스템·컴퓨터 조작) → ID-ER(외부 공개)

## 반복 노드가 들어간 경로 — 전체 2737개 (전체의 54%)

**INV-AT 3회 (툴루프)** — 120개
- DAC-CS(자격증명·비밀) → DAC-SRD(시스템·런타임 데이터) → INV-AT(응용 도구 호출) → DAC-UBD(사용자·업무 데이터) → INV-AT(응용 도구 호출) → DAC-UBD(사용자·업무 데이터) → INV-AT(응용 도구 호출)
- DAC-SRD(시스템·런타임 데이터) → INV-AT(응용 도구 호출) → DAC-UBD(사용자·업무 데이터) → INV-AT(응용 도구 호출) → DAC-UBD(사용자·업무 데이터) → INV-AT(응용 도구 호출)

**ENT-II 2회 (재진입)** — 1199개
- DAC-CS(자격증명·비밀) → EXE-SSE(Shell·명령 실행) → PST-CFG(지속 설정·규칙 잔류) → ENT-II(간접입력) → PST-KB(지식베이스 잔류) → ENT-II(간접입력)
- DAC-CS(자격증명·비밀) → EXE-SSE(Shell·명령 실행) → PST-CFG(지속 설정·규칙 잔류) → ENT-II(간접입력) → PST-KB(지식베이스 잔류) → ENT-II(간접입력) → DAC-UBD(사용자·업무 데이터)

**HD-UI 2회 (사용자 유도 반복)** — 141개
- DAC-CS(자격증명·비밀) → EXE-SSE(Shell·명령 실행) → PST-CFG(지속 설정·규칙 잔류) → ENT-II(간접입력) → HD-UI(사용자 유도) → HD-UI(사용자 유도)
- DAC-CS(자격증명·비밀) → EXE-SSE(Shell·명령 실행) → PST-CFG(지속 설정·규칙 잔류) → ENT-II(간접입력) → HD-UI(사용자 유도) → HD-UI(사용자 유도) → ID-ER(외부 공개)
