"""平台临时目录：系统盘满时改到 NAS 等可写路径."""
from __future__ import annotations

import os
import tempfile
from pathlib import Path


def configure_platform_temp_dir() -> Path | None:
    """
    将 Python / 标准库临时文件目录指到 PLATFORM_TEMP_DIR。

    设置 TMPDIR、TEMP、TMP 及 tempfile.tempdir，影响 tempfile、部分解压/下载逻辑。
    在 settings 加载 .env 之后尽早调用。
    """
    raw = os.environ.get("PLATFORM_TEMP_DIR", "").strip()
    if not raw:
        return None

    path = Path(raw).expanduser().resolve()
    path.mkdir(parents=True, exist_ok=True)

    path_str = str(path)
    for key in ("TMPDIR", "TEMP", "TMP"):
        os.environ[key] = path_str
    tempfile.tempdir = path_str
    return path
