#!/usr/bin/env python3
"""코드 → 한국어/영문 라벨 (Taxonomy v7). 출력 가독성용."""

# Element 코드 → (한국어, 영문)
ELEMENT = {
    "E1": ("진입", "Entry"), "E2": ("편입", "Integration"), "E3": ("권한·권위", "Privilege"),
    "E4": ("데이터 접근", "Data Access"), "E5": ("호출", "Invocation"), "E6": ("실행", "Execution"),
    "E7": ("상태 변경", "State Change"), "E8": ("지속화", "Persistence"),
    "E9": ("정보 공개", "Disclosure"), "E10": ("인간 의존", "Human Dependency"),
}

# Subcategory 코드 → (한국어, 영문)
SUBCAT = {
    "ENT-DI": ("직접입력", "Direct Input"),
    "ENT-II": ("간접입력", "Indirect Input"),
    "INT-EC": ("실행형 편입", "Executable Component"),
    "INT-CR": ("설정·규칙 편입", "Config·Rule"),
    "INT-MT": ("모델·템플릿 편입", "Model·Template"),
    "PA-GA": ("부여 권한", "Granted Authority"),
    "PA-CT": ("자격증명·토큰", "Credential·Token"),
    "PA-ACB": ("접근통제 우회", "Access-Control Bypass"),
    "DAC-UBD": ("사용자·업무 데이터", "User·Business Data"),
    "DAC-CS": ("자격증명·비밀", "Credential·Secret"),
    "DAC-SRD": ("시스템·런타임 데이터", "System·Runtime Data"),
    "INV-AT": ("응용 도구 호출", "Application Tool"),
    "INV-SCU": ("시스템·컴퓨터 조작", "System·Computer-Use"),
    "INV-CAI": ("제어·관리 인터페이스", "Control·Admin Interface"),
    "EXE-SE": ("코드·스크립트 실행", "Code·Script Execution"),
    "EXE-SSE": ("Shell·명령 실행", "Shell·Command Execution"),
    "SC-SYS": ("시스템·설정 상태변경", "System·Config State"),
    "SC-DAT": ("데이터·파일 상태변경", "Data·File State"),
    "SC-BIZ": ("업무·거래 상태변경", "Business·Transaction State"),
    "PST-MEM": ("세션·메모리 잔류", "Session·Memory Residue"),
    "PST-KB": ("지식베이스 잔류", "Knowledge-base Residue"),
    "PST-CFG": ("지속 설정·규칙 잔류", "Persistent Config Residue"),
    "ID-RG": ("결과 생성", "Result Generation"),
    "ID-ER": ("외부 공개", "External Release"),
    "HD-UI": ("사용자 유도", "User Inducement"),
    "HD-UAD": ("사용자 승인·판단", "User Approval·Decision"),
}


def ko(code: str) -> str:
    d = ELEMENT if code.startswith("E") and "-" not in code else SUBCAT
    return d.get(code, (code, ""))[0]


def label(code: str) -> str:
    """예: 'ENT-II(간접입력)'"""
    return f"{code}({ko(code)})"


def path_str(seq) -> str:
    """예: 'ENT-II(간접입력) → INV-AT(응용 도구 호출) → ...'"""
    return " → ".join(label(c) for c in seq)
