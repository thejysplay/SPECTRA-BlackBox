#!/usr/bin/env python3
"""
정본 26 CS 관측 시퀀스 (확정 스펙 v7 · 부록 A).

⚠ 이 파일이 시퀀스의 단일 출처(single source of truth). HTML 요약 테이블 파싱 금지
   (CS0063·CS0066 분기가 요약행에 없어 20노드/47엣지 버그 발생 — 스펙 §3·§8).

노드 = Subcategory(약자). Element(E1~E10)는 범주 라벨일 뿐 노드 아님(스펙 §2).
분기 케이스는 trunk + branches 로 저장. 전개 시 각 branch → (trunk+branch) 경로 1개.
branches[0] 을 주 경로(main)로 둔다(부록 A 표기 순서 첫째).
"""

# 선형(단일 경로) 24건
LINEAR = {
    "CS0016": ["ENT-DI", "INV-SCU", "EXE-SE", "DAC-CS", "ID-RG"],
    "CS0020": ["ENT-II", "HD-UI", "HD-UI", "ID-ER"],
    "CS0021": ["ENT-II", "ID-RG", "ID-ER"],
    "CS0024": ["ENT-II", "PST-KB", "ENT-II", "ID-RG", "ID-ER"],
    "CS0026": ["ENT-II", "PST-KB", "ENT-II", "ID-RG"],
    "CS0029": ["ENT-II", "ID-RG", "ID-ER"],
    "CS0035": ["ENT-II", "PST-KB", "ENT-II", "DAC-CS", "ID-RG", "HD-UI", "ID-ER"],
    "CS0037": ["ENT-II", "INV-AT", "DAC-UBD", "INV-AT", "DAC-UBD", "INV-AT", "ID-ER"],
    "CS0038": ["ENT-II", "PST-CFG", "ENT-II", "INV-AT", "DAC-UBD"],
    "CS0039": ["ENT-II", "INV-AT", "PA-GA", "DAC-UBD", "INV-AT", "ID-ER"],
    "CS0040": ["ENT-II", "PST-MEM"],
    "CS0041": ["INT-CR", "PST-CFG", "ENT-II", "ID-RG"],
    "CS0045": ["ENT-II", "INV-SCU", "DAC-CS", "EXE-SSE", "ID-ER"],
    "CS0046": ["ENT-II", "INV-SCU", "EXE-SSE", "SC-DAT"],
    "CS0047": ["INT-EC", "ENT-DI", "INV-SCU", "EXE-SSE", "SC-DAT"],
    "CS0049": ["INT-EC", "PST-CFG", "INV-AT", "HD-UAD", "EXE-SSE"],
    "CS0051": ["ENT-II", "INV-AT", "EXE-SSE", "PST-CFG", "ENT-II", "INV-SCU", "ID-ER"],
    "CS0052": ["ENT-DI", "INV-SCU", "EXE-SE"],
    "CS0054": ["INT-EC", "INV-AT", "INV-SCU", "DAC-CS", "DAC-SRD", "INV-AT", "ID-ER"],
    "CS0055": ["ENT-II", "INV-SCU", "EXE-SSE"],
    "CS0059": ["ENT-II", "PST-KB", "ENT-II", "DAC-UBD", "ID-ER"],
    "CS0061": ["ENT-II", "INV-AT", "ID-ER"],
    "CS0062": ["ENT-DI", "INV-AT", "EXE-SE"],
    "CS0067": ["ENT-II", "INV-SCU", "DAC-CS", "ID-RG"],
}

# 분기 2건 (trunk + branches). branches[0] = 주 경로.
BRANCH = {
    "CS0063": {
        "trunk": ["ENT-II", "PST-MEM", "ENT-II"],
        "branches": [
            ("F 데이터 유출", ["INV-AT", "PA-GA", "DAC-UBD", "ID-ER"]),
            ("B 데이터 파괴", ["INV-AT", "PA-GA", "SC-BIZ"]),
            ("C 물리 제어", ["INV-AT", "PA-GA", "SC-SYS"]),
            ("D 위치 추적", ["INV-SCU", "ID-ER"]),
            ("E 프라이버시 침해", ["INV-SCU"]),
            ("A 무결성 침해", ["ID-RG"]),
        ],
    },
    "CS0066": {
        # S03(악성 이메일이 inbox에 배치)은 Agent 미관여 = 공격자 준비 → 미매핑.
        # 실제 진입은 S04(요약 요청 시 검색·실행) 1회. 재유입 케이스(CS0024·26·35·38·59)는
        # 전부 ENT-II 사이에 PST가 있는데 CS0066만 PST 없이 ENT-II 2연속이던 것을 정정(진입 1회).
        # → ENT-II→ENT-II self-edge(유일 근거 CS0066) 소멸: edge 49→48 · 관측 103→102.
        "trunk": ["ENT-II"],
        "branches": [
            ("유출", ["INV-AT", "DAC-UBD", "ID-ER"]),
            ("지속 (메모리 변조)", ["PST-MEM"]),
            ("재배포 (측면 이동)", ["INV-AT", "DAC-UBD", "INV-AT", "ID-ER"]),
        ],
    },
}

SUB_TO_ELEMENT = {
    "ENT": ("E1", "진입"), "INT": ("E2", "편입"), "PA": ("E3", "권한·권위"),
    "DAC": ("E4", "데이터접근"), "INV": ("E5", "호출"), "EXE": ("E6", "실행"),
    "SC": ("E7", "상태변경"), "PST": ("E8", "지속화"), "ID": ("E9", "정보공개"),
    "HD": ("E10", "인간의존"),
}


def element_of(sub: str) -> str:
    return SUB_TO_ELEMENT[sub.split("-")[0]][0]


def expand_flows(expand_branches: bool = True):
    """{cid: [flow, ...]} 반환. flow = subcat 리스트.
    expand_branches=True → 분기별 (trunk+branch) 전개. False → 주 경로(branch[0])만."""
    out = {}
    for cid, seq in LINEAR.items():
        out[cid] = [list(seq)]
    for cid, spec in BRANCH.items():
        trunk = spec["trunk"]
        brs = spec["branches"] if expand_branches else spec["branches"][:1]
        out[cid] = [trunk + b for _, b in brs]
    return out
