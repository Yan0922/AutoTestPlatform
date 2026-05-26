"""从平台数据集（数据池）生成 K2 所需的 .scp / .src 文件."""
from __future__ import annotations

import json
import shutil
from collections import defaultdict
from pathlib import Path

from django.conf import settings

from ..audio_utils import resolve_media_path
from ..models import Audio, Dataset

from .config import task_staging_dir
from .lang_mapping import (
    k2_scp_filename,
    k2_src_filename,
    platform_lang_to_k2_scp_lang,
)


def _sanitize_dir_name(name: str) -> str:
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in (name or "dataset"))[:40]


def get_dataset_staging_dir(task_id: int, dataset: Dataset) -> Path:
    return task_staging_dir(task_id) / f"dataset_{dataset.id}_{_sanitize_dir_name(dataset.name)}"


def build_scp_src_for_dataset(task_id: int, dataset: Dataset, audios: list[Audio]) -> tuple[Path, list[str]]:
    """
    为单个数据集生成 staging 目录及 scp/src 文件。

    返回 (staging_dir, k2_scp_lang_list)。
    """
    staging_dir = get_dataset_staging_dir(task_id, dataset)
    if staging_dir.exists():
        shutil.rmtree(staging_dir)
    staging_dir.mkdir(parents=True, exist_ok=True)

    grouped: dict[str, list[Audio]] = defaultdict(list)
    for audio in audios:
        k2_lang = platform_lang_to_k2_scp_lang(audio.language)
        grouped[k2_lang].append(audio)

    index_map: dict[str, dict[str, int]] = {}
    skipped: list[dict] = []

    for k2_lang, items in grouped.items():
        scp_path = staging_dir / k2_scp_filename(k2_lang)
        src_path = staging_dir / k2_src_filename(k2_lang)
        lang_index_map: dict[str, int] = {}

        with scp_path.open("w", encoding="utf-8") as f_scp, src_path.open("w", encoding="utf-8") as f_src:
            for idx, audio in enumerate(items):
                wav_path = resolve_media_path(audio.audio_path)
                if not wav_path or not wav_path.is_file():
                    skipped.append({"audio_id": audio.id, "name": audio.name, "reason": "音频文件不存在"})
                    continue
                idx_str = str(idx)
                f_scp.write(f"{idx_str} {wav_path.as_posix()}\n")
                f_src.write(f"{idx_str} {(audio.ref_text or '').strip()}\n")
                lang_index_map[idx_str] = audio.id

        if lang_index_map:
            index_map[k2_lang] = lang_index_map

    meta = {
        "task_id": task_id,
        "dataset_id": dataset.id,
        "dataset_name": dataset.name,
        "index_map": index_map,
        "skipped": skipped,
        "media_root": str(Path(settings.MEDIA_ROOT).resolve()),
    }
    (staging_dir / "index_map.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    if not index_map:
        raise ValueError(f"数据集「{dataset.name}」没有可用的音频文件，无法生成 scp/src")

    return staging_dir, sorted(index_map.keys())
