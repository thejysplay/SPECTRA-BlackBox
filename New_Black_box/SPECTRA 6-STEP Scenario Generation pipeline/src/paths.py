# -*- coding: utf-8 -*-
"""경로·API키 해석 (머신 독립).

기존 스크립트는 /home/kitesu/... 절대경로를 하드코딩했다. 계정이 바뀌면 전부 깨지므로
여기서 한 번만 해석한다. 우선순위는 전부 `환경변수 → 레포 내부 → 레거시 경로`.

환경변수
  SPECTRA_AGENTDOJO   개조 AgentDojo 루트 (기본: 레포의 SPECTRA_AgentDojo/agentdojo)
  SPECTRA_ENV_FILE    API 키가 든 .env 경로 (없으면 이미 export 된 환경변수만 사용)
"""
import os
import sys
from pathlib import Path

# 이 파일 = <PIPE_ROOT>/src/paths.py
PIPE_ROOT = Path(__file__).resolve().parent.parent
# <REPO_ROOT>/New_Black_box/<PIPE_ROOT>
REPO_ROOT = PIPE_ROOT.parent.parent

DATA = PIPE_ROOT / "data"

_LEGACY_ADOJO = Path("/home/kitesu/SPECTRA-BlackBox/논문실험/agentdojo")


def agentdojo_root() -> Path:
    """개조 AgentDojo 루트. 없으면 RuntimeError."""
    env = os.environ.get("SPECTRA_AGENTDOJO")
    cands = [Path(env)] if env else []
    cands += [REPO_ROOT / "SPECTRA_AgentDojo" / "agentdojo", _LEGACY_ADOJO]
    for c in cands:
        if (c / "src" / "agentdojo").is_dir():
            return c
    raise RuntimeError(
        "개조 AgentDojo를 찾지 못했다. SPECTRA_AGENTDOJO 로 경로를 지정하라.\n"
        "  확인한 경로: " + " · ".join(str(c) for c in cands))


def use_agentdojo() -> Path:
    """agentdojo 를 import 가능하게 sys.path 에 얹고 루트를 반환."""
    root = agentdojo_root()
    src = root / "src"
    for p in (str(src), str(root)):
        if p not in sys.path:
            sys.path.insert(0, p)
    return root


def load_env_keys() -> list:
    """.env 의 *_API_KEY / *_BASE_URL / *_API_BASE 를 환경변수로 올린다.

    이미 환경에 있는 키는 덮어쓰지 않는다(export 가 .env 보다 우선).
    .env 가 없어도 에러 아님 — export 만으로 쓰는 게 정상 경로다.
    """
    env = os.environ.get("SPECTRA_ENV_FILE")
    cands = [Path(env)] if env else []
    cands += [REPO_ROOT / ".env", PIPE_ROOT / ".env", Path.home() / ".spectra.env"]
    loaded = []
    for c in cands:
        try:
            if not c.is_file():
                continue
            for ln in c.read_text(encoding="utf-8").splitlines():
                ln = ln.strip()
                if not ln or ln.startswith("#") or "=" not in ln:
                    continue
                k, v = ln.split("=", 1)
                k = k.strip()
                if k.endswith(("_API_KEY", "_BASE_URL", "_API_BASE")) and not os.environ.get(k):
                    os.environ[k] = v.strip().strip('"').strip("'")
                    loaded.append(k)
            break
        except OSError:
            continue        # 권한 없는 경로(예: 타 계정 홈)는 조용히 건너뜀
    if os.environ.get("GEMINI_API_KEY"):
        os.environ.setdefault("GOOGLE_API_KEY", os.environ["GEMINI_API_KEY"])
    return loaded


def require(*keys):
    """필요한 키가 없으면 무엇을 export 해야 하는지 알려주고 종료."""
    missing = [k for k in keys if not os.environ.get(k)]
    if missing:
        sys.exit("[중단] 환경변수 누락: " + ", ".join(missing) +
                 "\n  export 하거나 SPECTRA_ENV_FILE=<.env 경로> 로 지정하라.")
