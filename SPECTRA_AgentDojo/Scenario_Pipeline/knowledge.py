# -*- coding: utf-8 -*-
"""
Threat Knowledge 로더 + 조회 인덱스
====================================================================================================
threat_knowledge.yaml(정본)을 읽어 파이프라인이 쓰기 좋은 인덱스를 만든다.
- INSTANCE → (Subcategory, Element) 부모 조회 (STEP2 ②-1: Instance→Element 는 코드가 결정)
- Element → 그 Element 산하 Instance 목록
- ATTACK_GOALS / CASE_STUDIES 접근자
과도한 추상화 없이 단순 dict + 헬퍼 함수만.
"""
from pathlib import Path
import yaml

KNOW_PATH = Path(__file__).parent.parent / "Threat_Knowledge" / "threat_knowledge.yaml"


def load(path=None):
    K = yaml.safe_load(Path(path or KNOW_PATH).read_text(encoding="utf-8"))
    return Knowledge(K)


class Knowledge:
    def __init__(self, K):
        self.matrix = K["THREAT_MATRIX"]
        self.goals = K["ATTACK_GOALS"]
        self.cases = K["CASE_STUDIES"]
        # 인덱스: instance_id → {"sub","element","label","source"}
        self.instance_parent = {}
        self.element_instances = {e: [] for e in self.matrix}
        for e, ev in self.matrix.items():
            for sub, sv in ev["subcategories"].items():
                for iid, inst in sv["instances"].items():
                    self.instance_parent[iid] = {"sub": sub, "element": e,
                                                 "label": inst.get("name_ko", iid), "name_en": inst.get("name_en", ""),
                                                 "description": inst.get("description", "")}
                    self.element_instances[e].append(iid)
        # instance → 이 Instance 가 실제 관측된 Case Study 목록 (의미 근거)
        self.instance_cases = {}
        for cid, c in self.cases.items():
            for iid in c.get("instances", []):
                self.instance_cases.setdefault(iid, []).append(cid)

    # ── 조회 헬퍼 ──────────────────────────────────────────────────────────────
    def element_of(self, instance_id):
        """②-1: Instance → 부모 Element (코드 결정, LLM 불필요)."""
        p = self.instance_parent.get(instance_id)
        return p["element"] if p else None

    def elements_of(self, instance_ids):
        """matched instance 집합 → 커버되는 Element 집합."""
        return {self.element_of(i) for i in instance_ids if self.element_of(i)}

    def valid_instance(self, instance_id):
        return instance_id in self.instance_parent

    def all_instances(self):
        return list(self.instance_parent)

    def goal(self, gid):
        return self.goals[gid]

    def cases_by_goal(self, gid):
        return {cid: c for cid, c in self.cases.items() if c["attack_goal"] == gid}

    # ── PHASE1 지원: 프롬프트용 170 Instance 카탈로그 / 매칭결과 → 필터링 Matrix ──
    def instance_catalog(self, role_hints=None):
        """LLM 에 주는 170 Instance 후보 목록(텍스트). Element 단위 역할 힌트 포함."""
        role_hints = role_hints or {}
        lines = []
        for e, ev in self.matrix.items():
            hint = role_hints.get(e, "")
            lines.append(f"\n[{e}] {ev['name_ko']} ({ev['name_en']})" + (f"  ⟪{hint}⟫" if hint else ""))
            for sub, sv in ev["subcategories"].items():
                ids = "  ".join(f"{iid}={inst['name_ko']}" for iid, inst in sv["instances"].items())
                lines.append(f"  {sub} {sv['name_ko']}: {ids}")
        return "\n".join(lines)

    def subcategories(self):
        """PHASE1 batching 단위 (dict). Element/Subcategory 의 한글명·영문명·description 포함(교수님 표현)."""
        for e, ev in self.matrix.items():
            for sub, sv in ev["subcategories"].items():
                insts = [(iid, inst["name_ko"], inst.get("description", "")) for iid, inst in sv["instances"].items()]
                yield {"element": e, "e_ko": ev["name_ko"], "e_en": ev["name_en"], "e_desc": ev["description"],
                       "sub": sub, "s_ko": sv["name_ko"], "s_en": sv["name_en"], "s_desc": sv["description"],
                       "instances": insts}

    def instance_meaning(self, iid, max_cases=2):
        """Instance 의미 근거: 실제 관측 Case Study 이름(있으면) / 없으면 범용 확장 표시."""
        cases = self.instance_cases.get(iid, [])
        if not cases:
            return "범용 확장(Case Study 미관측)"
        names = [f"{cid.replace('AML.','')}({' '.join(self.cases[cid]['name'].split()[:6])})" for cid in cases[:max_cases]]
        extra = f" 외 {len(cases) - max_cases}건" if len(cases) > max_cases else ""
        return "실제 관측: " + "; ".join(names) + extra

    def matched_matrix(self, matched_ids):
        """매칭된 Instance 만 남긴 THREAT_MATRIX (E→Subcategory→Instance 구조 그대로)."""
        matched = set(matched_ids)
        out = {}
        for e, ev in self.matrix.items():
            subs = {}
            for sub, sv in ev["subcategories"].items():
                keep = {iid: inst for iid, inst in sv["instances"].items() if iid in matched}
                if keep:
                    subs[sub] = {"name_ko": sv["name_ko"], "name_en": sv["name_en"],
                                 "description": sv["description"], "instances": keep}
            if subs:
                out[e] = {"name_ko": ev["name_ko"], "name_en": ev["name_en"],
                          "description": ev["description"], "subcategories": subs}
        return out
