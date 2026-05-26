"""音频文件工具：路径解析、时长读取、行业字段映射."""
from __future__ import annotations

import contextlib
import wave
from pathlib import Path

from django.conf import settings

from .models import INDUSTRY_CHOICES

INDUSTRY_LABEL_TO_CODE = {label: code for code, label in INDUSTRY_CHOICES}
INDUSTRY_CODE_SET = {code for code, _ in INDUSTRY_CHOICES}


def resolve_industry(value: str) -> str:
    """将中文行业名或 code 转为数据库存储的 industry code."""
    v = (value or "").strip()
    if not v:
        return "unknown"
    if v in INDUSTRY_CODE_SET:
        return v
    return INDUSTRY_LABEL_TO_CODE.get(v, "unknown")


def get_wav_duration(path: Path) -> float:
    """读取 wav 时长(秒)，失败返回 0."""
    try:
        with contextlib.closing(wave.open(str(path), "rb")) as wf:
            frames = wf.getnframes()
            rate = wf.getframerate()
            if rate <= 0:
                return 0.0
            return round(frames / float(rate), 2)
    except Exception:
        return 0.0


def resolve_media_path(audio_path: str) -> Path | None:
    """将 audio_path(URL 或相对路径) 解析为磁盘上的文件路径."""
    if not audio_path:
        return None
    path = str(audio_path).strip().replace("\\", "/")

    media_url = settings.MEDIA_URL.rstrip("/") + "/"
    if path.startswith(media_url):
        rel = path[len(media_url):]
    elif path.startswith("/media/"):
        rel = path[len("/media/"):]
    elif path.startswith("media/"):
        rel = path[len("media/"):]
    else:
        rel = path.lstrip("/")

    return Path(settings.MEDIA_ROOT) / rel


def detect_duration_from_path(audio_path: str) -> float:
    """根据 audio_path 自动识别音频时长."""
    file_path = resolve_media_path(audio_path)
    if not file_path or not file_path.is_file():
        return 0.0
    return get_wav_duration(file_path)
