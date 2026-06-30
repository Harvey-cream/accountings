"""从 accountsystem/.env 加载环境变量（.env 已在 .gitignore，不会进仓库）。"""

import os
from pathlib import Path

from dotenv import load_dotenv

_ROOT = Path(__file__).resolve().parent.parent
_LOADED = False


def load_project_dotenv() -> None:
    global _LOADED
    if _LOADED:
        return
    env_path = _ROOT / ".env"
    if env_path.is_file():
        load_dotenv(env_path)
    _LOADED = True


def env_str(name: str, default: str = "") -> str:
    load_project_dotenv()
    return os.getenv(name, default).strip()
