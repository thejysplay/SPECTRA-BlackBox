#!/usr/bin/env python3
"""
v7 인스턴스 매트릭스 → 구조화 JSON (STEP 6 입력용)

새 매핑 HTML의 '공격요소 Instance 분류 표'에서
  Element → Subcategory → Instance(관찰●/확장○ + 근거 CS)
를 뽑아 data/instances_v7.json 으로 저장.
"""
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "instances_v7.json"


def _find_v7_html():
    # 파일명이 공백('Case Mapping v7')이든 언더스코어('Case_Mapping_v7')든 매칭
    for pat in ("*apping*v7*.html", "*apping*V7*.html", "*v7*.html", "*V7*.html"):
        m = sorted(ROOT.glob(pat))
        if m:
            return m[0]
    raise FileNotFoundError("v7 Case Mapping HTML을 폴더에서 찾을 수 없음")


HTML = _find_v7_html()

PREFIX_ELEMENT = {
    "ENT": ("E1", "진입"), "INT": ("E2", "편입"), "PA": ("E3", "권한·권위"),
    "DAC": ("E4", "데이터 접근"), "INV": ("E5", "호출"), "EXE": ("E6", "실행"),
    "SC": ("E7", "상태 변경"), "PST": ("E8", "지속화"), "ID": ("E9", "정보 공개"),
    "HD": ("E10", "인간 의존"), "CM": ("MANIP", "조작 유형(케이스 속성)"),
}


def clean(s):
    return html.unescape(re.sub(r"<[^>]+>", "", s)).strip()


def main():
    raw = HTML.read_text(encoding="utf-8", errors="ignore")
    s = raw.find("공격요소 Instance 분류 표")
    e = raw.find("전체 Attack Sequence 일람")
    sec = raw[s:e]

    # subttl 블록 단위로 분할
    chunks = re.split(r'(?=<div class="subttl")', sec)
    subcats = {}
    for ch in chunks:
        mcode = re.search(r"\[([A-Z]+-[A-Z]+)\]", ch)
        if not mcode:
            continue
        code = mcode.group(1)
        # subcategory 한글/영문 이름
        mname = re.search(r'class="subttl"[^>]*>(.*?)<span class="subab">', ch, re.S)
        sub_ko = clean(mname.group(1)) if mname else ""
        men = re.search(r'class="suben">(.*?)</div>', ch, re.S)
        sub_en = clean(men.group(1)) if men else ""
        # li 인스턴스들
        insts = []
        for li in re.finditer(
            r'<li class="it (it-cs|it-ext)"[^>]*title="([^"]*)">(.*?)</li>', ch, re.S
        ):
            kind, title, body = li.group(1), li.group(2), li.group(3)
            en = re.search(r'class="ien">(.*?)</span>', body)
            ko = re.search(r'class="iko">(.*?)</span>', body)
            ev = re.findall(r"CS\d+", title)
            insts.append({
                "en": clean(en.group(1)) if en else "",
                "ko": clean(ko.group(1)) if ko else "",
                "observed": kind == "it-cs",
                "evidence": ev,
            })
        prefix = code.split("-")[0]
        elem, elem_ko = PREFIX_ELEMENT.get(prefix, ("?", "?"))
        subcats[code] = {
            "element": elem, "element_ko": elem_ko,
            "subcategory_ko": sub_ko, "subcategory_en": sub_en,
            "instances": insts,
        }

    n_inst = sum(len(v["instances"]) for v in subcats.values())
    n_obs = sum(1 for v in subcats.values() for i in v["instances"] if i["observed"])
    payload = {
        "n_subcategories": len(subcats),
        "n_instances": n_inst, "n_observed": n_obs, "n_extension": n_inst - n_obs,
        "subcategories": subcats,
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"서브카테고리 {len(subcats)} · 인스턴스 {n_inst} (관찰 {n_obs} / 확장 {n_inst-n_obs})")
    print(f"→ {OUT.relative_to(ROOT)}")
    # 샘플
    print("\n샘플:")
    for code in ["ENT-DI", "DAC-CS", "ID-ER", "CM-AM"]:
        if code in subcats:
            v = subcats[code]
            print(f"  {code}({v['subcategory_ko']}):")
            for i in v["instances"][:3]:
                dot = "●" if i["observed"] else "○"
                print(f"     {dot} {i['en']:28s} 근거={i['evidence']}")


if __name__ == "__main__":
    main()
