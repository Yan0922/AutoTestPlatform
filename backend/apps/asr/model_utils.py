"""ASR 模型目录路径工具."""
from __future__ import annotations

import os
import re
import shutil
from pathlib import Path

from django.conf import settings

from .models import AsrModel, AsrModelFile

_INVALID_DIR_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def sanitize_model_dir_name(name: str) -> str:
    """将模型名称转为可用于文件夹名的字符串."""
    s = (name or "").strip()
    s = _INVALID_DIR_CHARS.sub("_", s)
    s = s.replace("..", "_").strip(". ")
    return s or "unnamed"


def _dir_path_taken(rel_path: str, exclude_id: int | None = None) -> bool:
    qs = AsrModel.objects.filter(dir_path=rel_path, status=1)
    if exclude_id is not None:
        qs = qs.exclude(id=exclude_id)
    if qs.exists():
        return True
    return (Path(settings.MEDIA_ROOT) / rel_path).exists()


def build_model_dir_path(name: str, model_id: int) -> str:
    """生成 models/asr/{模型名} 形式的相对路径；重名时追加 _{id}."""
    slug = sanitize_model_dir_name(name)
    candidate = f"models/asr/{slug}"
    if not _dir_path_taken(candidate, exclude_id=model_id):
        return candidate
    return f"models/asr/{slug}_{model_id}"


def persist_model_files_from_dir(model_instance: AsrModel, source_dir: Path) -> int:
    """将本地目录中的模型文件复制到 media 并写入 asr_model_file 表."""
    base_dir = Path(settings.MEDIA_ROOT) / model_instance.dir_path
    base_dir.mkdir(parents=True, exist_ok=True)
    count = 0
    for file_path in source_dir.rglob("*"):
        if not file_path.is_file():
            continue
        rel = file_path.relative_to(source_dir).as_posix()
        dest = base_dir / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(file_path, dest)
        size = dest.stat().st_size
        AsrModelFile.objects.create(
            model=model_instance,
            file_name=os.path.basename(rel),
            file_size=size,
            file_path=f"{model_instance.dir_path}/{rel}",
        )
        count += 1
    return count
