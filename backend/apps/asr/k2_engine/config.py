"""K2 引擎配置."""
from __future__ import annotations

import os
import sys
from pathlib import Path

from django.conf import settings


def k2_enabled() -> bool:
    return os.environ.get("K2_ENGINE_ENABLED", "0") == "1"


def k2_project_root() -> Path | None:
    raw = os.environ.get("K2_PROJECT_ROOT", "").strip()
    if raw:
        return Path(raw).resolve()
    # 默认：仓库根目录下的 model-test
    base = Path(settings.BASE_DIR).resolve().parent
    candidate = base / "model-test"
    return candidate if candidate.is_dir() else None


def k2_pro_dpath() -> Path | None:
    """k2_asr_model_test 目录（testAsr 工作目录）."""
    root = k2_project_root()
    if not root:
        return None
    candidate = root / "k2_asr_model_test"
    return candidate if candidate.is_dir() else None


def testasr_bin() -> Path | None:
    explicit = os.environ.get("TESTASR_BIN", "").strip()
    if explicit:
        p = Path(explicit)
        return p if p.is_file() else None
    pro = k2_pro_dpath()
    if not pro:
        return None
    candidate = pro / "testAsr"
    return candidate if candidate.is_file() else None


def staging_root() -> Path:
    raw = os.environ.get("K2_STAGING_DIR", "").strip()
    if raw:
        return Path(raw).resolve()
    return Path(settings.MEDIA_ROOT) / "k2_staging"


def sanitize_staging_name(name: str, *, max_len: int = 60) -> str:
    """将任务名等转为安全的目录名."""
    cleaned = "".join(c if c.isalnum() or c in "-_" else "_" for c in (name or "task"))
    return cleaned[:max_len] or "task"


def task_staging_dir(task_name: str) -> Path:
    """K2 任务 staging 根目录，使用带时间后缀的任务名，例如 test_20260527_1438."""
    return staging_root() / sanitize_staging_name(task_name)


def ensure_k2_on_path() -> Path | None:
    root = k2_project_root()
    if not root:
        return None
    root_str = str(root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)
    return root


def is_k2_python_ready() -> bool:
    """model-test WER 脚本所需的 Python 依赖是否已安装."""
    try:
        import jiwer  # noqa: F401
        import MeCab  # noqa: F401
        import pandas  # noqa: F401
        import ujson  # noqa: F401
        from loguru import logger  # noqa: F401
        from pecab import PeCab  # noqa: F401
        from pythainlp.tokenize import word_tokenize  # noqa: F401
        from whisper_normalizer.english import EnglishTextNormalizer  # noqa: F401
    except ImportError:
        return False
    return True


def is_k2_available() -> bool:
    """是否启用且 testAsr 可执行文件存在（Linux 服务器环境）."""
    if not k2_enabled():
        return False
    if not k2_project_root() or not k2_pro_dpath():
        return False
    if testasr_bin() is None:
        return False
    return is_k2_python_ready()
