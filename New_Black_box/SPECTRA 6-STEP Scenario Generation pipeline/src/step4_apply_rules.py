#!/usr/bin/env python3
"""
STEP 4 (v7): 룰 필터 — 말 안 되는 경로 제거 (룰 하나씩 추가)

현재 룰: R0 유효시작 · R19 유효종점(=관측된 공격 목표)
관측 31개 흐름(=실제 26 사건)은 어떤 룰에도 안 지워져야 정상.
출력: data/step4_scenarios.json · data/step4_scenarios.md
"""
import json
from collections import defaultdict
from pathlib import Path

from sequences_v7 import element_of, expand_flows
from labels import ko, path_str

ROOT = Path(__file__).resolve().parent.parent
PATHS_IN = ROOT / "data" / "step3_paths.json"
OUT = ROOT / "data" / "step4_scenarios.json"
OUT_MD = ROOT / "data" / "step4_scenarios.md"

# 관측된 종점(=공격 목표) 집합과 근거 케이스 — 데이터에서 도출
_FLOWS = expand_flows(True)
OBSERVED_ENDPOINTS = sorted({f[-1] for fs in _FLOWS.values() for f in fs})
END_EVIDENCE = defaultdict(set)
for _cid, _fs in _FLOWS.items():
    for _f in _fs:
        END_EVIDENCE[_f[-1]].add(_cid)

# 종점 → 공격 목표 이름
GOAL = {
    "ID-ER": "데이터 유출", "ID-RG": "결과물 노출·생성",
    "EXE-SE": "코드 실행", "EXE-SSE": "명령 실행",
    "SC-DAT": "데이터·파일 파괴·조작", "SC-BIZ": "업무·거래 조작", "SC-SYS": "시스템·기기 제어",
    "PST-MEM": "메모리 오염·지속", "DAC-UBD": "데이터 확보(지연형)", "INV-SCU": "기기 조작·프라이버시",
}


# ────────── 룰 ──────────
def r0_valid_start(path):
    """공격은 진입(E1)/편입(E2)에서 시작."""
    return element_of(path[0]) in ("E1", "E2")


def r19_valid_endpoint(path):
    """경로 끝이 실제 관측된 공격 목표(종점 10개) 중 하나여야 함(=목표 달성 완성)."""
    return path[-1] in OBSERVED_ENDPOINTS


def _derive_req_before():
    """관측 흐름에서 '각 원소 B가 나오면 그 앞에 항상 있던 원소'(교집합) 도출.
    손으로 안 짓고 데이터에서 뽑으므로 관측 31는 자동 보존.

    단, 진입(E1)/편입(E2)은 '시작 조건'이라 SR1이 이미 담당 → 선후 의존성에서 제외.
    E3(권한)·E7(상태변경)의 교집합에 뜨는 'E1 필수'는 표본 4개(CS 2~3건)에서 나온 과적합.
    반례: CS0049가 E1 없이 E2(편입)로만 시작해 실행(E6)까지 감 = E1 없는 체인이 실존.
    따라서 행위 원소(호출 E5 등)만 요건으로 남김 → {E3←E5, E6←E5, E7←E5}."""
    flows = [[element_of(n) for n in f] for fs in _FLOWS.values() for f in fs]
    req = {}
    for B in {e for f in flows for e in f}:
        befores = [set(f[:f.index(B)]) for f in flows if B in f]
        always = set.intersection(*befores) if befores else set()
        always -= {B, "E1", "E2"}   # 자기 자신 + 시작 원소(SR1 담당) 제외
        if always:
            req[B] = always
    return req


REQ_BEFORE = _derive_req_before()   # {E3:{E5}, E6:{E5}, E7:{E5}} — '실행·권한·상태변경 ← 호출'


def r_dep(path):
    """선후 의존성 — 각 원소 앞에 '반드시 있어야 할 원소'(REQ_BEFORE)가 먼저 나와야."""
    elems = [element_of(n) for n in path]
    for e, req in REQ_BEFORE.items():
        if e in elems and not req.issubset(set(elems[:elems.index(e)])):
            return False
    return True


# 우리 룰 체계 (SR = SPECTRA Rule). 괄호는 HTML 원 룰 대응.
RULES = [
    ("SR1", "유효 시작 — 진입(ENT)/편입(INT)에서만 시작 [관측 33 flow 첫 원소가 전부 E1/E2, 데이터 도출]", r0_valid_start),
    ("SR2", "유효 종점 — 관측된 공격 목표(종점 10개)로 끝남 [HTML R19]", r19_valid_endpoint),
    ("SR3", "선후 의존성(element) — 실행·권한·상태변경 ← 호출(E5) [HTML R1·R3~R12 통합]", r_dep),
]


def build_md(paths, survivors, observed, funnel):
    obs_kept = len(observed & set(survivors))
    md = []
    md += ["# STEP 4 — 룰 필터 (v7)", ""]

    # (1) HTML 21룰 전부에 대한 우리 처리
    md += ["## HTML 21개 룰 → 우리가 무엇으로 완료했나", "",
           "교수님 HTML의 STEP 4 = **6범주 21룰**. 각 룰을 v7에서 어떻게 처리했는지 전수 정리.", "",
           "상태 범례: **SR#**=우리 룰로 구현 · **STEP3/5**=다른 단계에서 처리 · **흡수**=SR3로 통합 · **생략**=초기 버전 미구현", "",
           "| 범주 | 룰 | 내용 | 우리 처리 |",
           "|---|---|---|---|",
           "| ① 시간 | R1 인과역전 | 유출 후 입력 | **SR3 흡수** (관측엣지라 역전 없음) |",
           "| ① 시간 | R2 피드백루프 | 무한 순환 | **STEP3** 반복상한이 처리 |",
           "| ② 권한 | R3 권한순서 | 접근 전 권한 | **SR3 흡수** (권한←호출) |",
           "| ② 권한 | R4 컨텍스트격리 | 공개→비공개 직접 | **SR3 부분** |",
           "| ② 권한 | R5 신뢰경계 | 비신뢰에 권한위임 | 생략 |",
           "| ② 권한 | R6 사용자의도 | 셸 앞 승인필요 | 생략 (관측상 강제 아님) |",
           "| ② 권한 | R7 암묵의존 | 동기 없는 접근 | **SR1 흡수** (U3 제거) |",
           "| ② 권한 | R8 입출력타입 | 타입 불일치 | 생략 (노드 단위 판정 난이) |",
           "| ③ 의존 | R9 흐름역전 | 실행 후 접근 | **SR3 흡수** |",
           "| ③ 의존 | R10 선행조건 | 지속화 앞 소스 | **SR3 흡수** |",
           "| ③ 의존 | R11 정보소스 | 유출 앞 데이터원 | **그래프구조+SR3** (엄격룰은 CS0020 때문에 불가) |",
           "| ③ 의존 | R12 출력생성 | 유출 앞 렌더링 | 생략 (DAC→유출 관측되어 강제 못함) |",
           "| ④ 능력 | R13 능력가용 | 도구 존재 여부 | **STEP5 이동** |",
           "| ④ 능력 | R14 상태메커니즘 | 메모리 지원 | **STEP5 이동** |",
           "| ④ 능력 | R15 플랫폼호환 | 플랫폼 지원 | **STEP5 이동** |",
           "| ⑤ 의미 | R16 상호배제 | 삭제→복원 모순 | 생략 (서브카테고리 단위 미포착) |",
           "| ⑤ 의미 | R17 의미모순 | 상태변화 없는 반복 | **STEP3** 반복상한 |",
           "| ⑤ 의미 | R18 중복검사 | 입력 직접반복 | **STEP3** 반복상한(ENT-II≤2) |",
           "| ⑥ 목표 | R19 목표달성 | 종점이 impact | **SR2 완료** |",
           "| ⑥ 목표 | R20 임팩트체인 | 호출 후 영향없음 | 보류 (SR4 시도했다 철회) |",
           "| ⑥ 목표 | R21 결과실현 | 출력만 상태변경X | **SR2 흡수** (ID-RG도 유효 목표) |",
           "",
           "**우리가 실제로 구현한 룰**: SR1(유효시작) · SR2(유효종점) · SR3(선후의존성). "
           "**STEP3에서 이미 처리**: R2·R17·R18. **STEP5로 이동**: R13·R14·R15. "
           "**초기 생략**: R5·R6·R8·R12·R16·R20.", ""]

    # (2) 퍼널
    md += ["## 적용 룰 & 퍼널", "",
           f"입력(STEP3) {len(paths)} → 생존 **{len(survivors)}** · 관측 31흐름 유지 {obs_kept}/{len(observed)}", "",
           "| 룰 | 설명 | 남음 | 제거 | 관측유지 |", "|---|---|---|---|---|"]
    for rid, desc, after, removed, okept in funnel:
        md.append(f"| {rid} | {desc} | {after} | {removed} | {okept}/{len(observed)} |")
    md.append("")

    # (2b) 선후 의존성 (관측 도출)
    md += ["## 선후 의존성 룰 (SR3) — 관측에서 도출", "",
           "26개 시퀀스에서 '각 원소가 나올 때 그 앞에 항상 있던 원소'(교집합)를 뽑음. "
           "단, 진입(E1)/편입(E2)은 시작 조건이라 SR1이 담당 → 제외.",
           "", "| 원소 | 앞에 반드시 있어야 |", "|---|---|"]
    for e, req in sorted(REQ_BEFORE.items()):
        md.append(f"| {e}({ko(e)}) | {', '.join(f'{r}({ko(r)})' for r in sorted(req))} |")
    md += ["", "즉 **실행·권한·상태변경 앞엔 호출(E5)**이 반드시 있어야 함. 이걸 어긴 경로를 제거.",
           "(과거 'E3·E7←진입(E1)' 조항은 표본 4개 과적합이라 제외 — CS0049가 E1 없이 실행까지 감이 반례. "
           "인과역전 R1도 여기 흡수: '앞에 있어야 할 게 없다'=순서 뒤집힘)", ""]

    # (3) 목표 = 종점 + 근거
    md += ["## 공격 목표 = 종점 (근거 케이스)", "",
           "종점(끝 노드)이 곧 그 시나리오의 공격 목표. 아래 10개가 실제 관측된 목표이고, "
           "근거 = 그 종점으로 끝난 실제 사건.", "",
           "| 종점 | 공격 목표 | 근거 케이스 |", "|---|---|---|"]
    for e in OBSERVED_ENDPOINTS:
        cases = ", ".join(sorted(END_EVIDENCE[e]))
        md.append(f"| {e}({ko(e)}) | {GOAL.get(e,'?')} | {cases} |")
    md.append("")

    # (4) 깊이로 위험 설명
    md += ["## 위험도는 '깊이'로 설명한다", "",
           "- 목표는 경로의 **끝(종점)으로 고정**한다.",
           "- 그 경로를 실제 에이전트로 돌려 **몇 단계까지 갔나 = 깊이**를 잰다.",
           "- **깊이 = 위험도.** 끝까지 가면 완전 위험, 중간에서 막히면 거기까지만 위험.",
           "- 예) 목표가 *유출*인 경로가 **데이터 확보까지만** 가고 유출에서 막힘 → "
           "\"데이터 확보까진 가능, 유출은 막힘\". **약한 고리 = 유출(전송) 단계.**",
           "- 멈춘 이유 구분: **방어(거부)** vs **능력 부족(도구 없음)**. 둘 다 '유출 실패'지만 "
           "앞만 진짜 방어이고 뒤는 우연히 안전한 것.", ""]

    # (5) 생존 예시
    md += ["## 생존 시나리오 예시 (⟵ = 실제 관측)", ""]
    for i, p in enumerate(sorted(survivors)[:25], 1):
        mark = "  ⟵ 실제 관측" if p in observed else ""
        md.append(f"{i}. {path_str(p)}{mark}")
    return "\n".join(md)


def main():
    d = json.loads(PATHS_IN.read_text(encoding="utf-8"))
    paths = [tuple(p.split("→")) for p in d["broad_paths"]]
    observed = {tuple(f) for fs in _FLOWS.values() for f in fs}

    print(f"입력(STEP3): {len(paths)}개 · 관측 흐름 {len(observed)}개 포함\n")
    print("===== 룰 적용 퍼널 =====")
    print(f"{'룰':6s} {'설명':42s} {'남음':>7s} {'제거':>7s} {'관측유지':>8s}")
    survivors = paths
    funnel = []
    for rid, desc, fn in RULES:
        before = len(survivors)
        survivors = [p for p in survivors if fn(p)]
        removed = before - len(survivors)
        okept = len(observed & set(survivors))
        funnel.append((rid, desc, len(survivors), removed, okept))
        print(f"{rid:6s} {desc:42s} {len(survivors):>7d} {removed:>7d} {okept:>4d}/{len(observed)}")

    obs_kept = observed & set(survivors)
    print(f"\n최종 생존: {len(survivors)}개 · 관측 31 유지: {len(obs_kept)}/{len(observed)} "
          f"{'✅' if len(obs_kept)==len(observed) else '❌'}")

    payload = {
        "rules_applied": [{"id": r, "desc": desc} for r, desc, _ in RULES],
        "input_count": len(paths), "surviving_count": len(survivors),
        "observed_kept": f"{len(obs_kept)}/{len(observed)}",
        "goal_endpoints": {e: {"goal": GOAL.get(e), "evidence": sorted(END_EVIDENCE[e])}
                           for e in OBSERVED_ENDPOINTS},
        "scenarios": ["→".join(p) for p in sorted(survivors)],
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    OUT_MD.write_text(build_md(paths, survivors, observed, funnel), encoding="utf-8")
    print(f"\n  → {OUT.relative_to(ROOT)} · {OUT_MD.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
