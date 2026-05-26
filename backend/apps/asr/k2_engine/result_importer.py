"""将 K2 测试输出 jsonl 解析并写入 test_audio_result / test_task_dataset."""
from __future__ import annotations

import json
from pathlib import Path

from django.db import transaction

from ..models import Audio, Dataset, TestAudioResult, TestTask, TestTaskDataset
from ..wer import compute_wer

from .lang_mapping import k2_result_key


def _load_index_map(staging_dir: Path) -> dict:
    meta_path = staging_dir / "index_map.json"
    if not meta_path.is_file():
        raise FileNotFoundError(f"缺少 index_map.json: {staging_dir}")
    return json.loads(meta_path.read_text(encoding="utf-8"))


def _find_latest_result_subdir(staging_dir: Path) -> Path | None:
    """查找 infer_batch_all 生成的带时间戳的结果子目录."""
    results_root = staging_dir / "results"
    if not results_root.is_dir():
        return None
    subdirs = [p for p in results_root.iterdir() if p.is_dir()]
    if not subdirs:
        return None
    return max(subdirs, key=lambda p: p.stat().st_mtime)


def _parse_result_jsonl(path: Path, result_key: str) -> dict[str, tuple[str, str]]:
    """返回 index_str -> (reference, hyp)."""
    parsed: dict[str, tuple[str, str]] = {}
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            item = json.loads(line)
            name = str(item.get("name", ""))
            ref = (item.get("reference") or "").strip()
            results = item.get("result") or {}
            hyp = (results.get(result_key) or results.get(result_key.replace("-", "")) or "").strip()
            if not hyp and isinstance(results, dict) and len(results) == 1:
                hyp = str(next(iter(results.values())) or "").strip()
            parsed[name] = (ref, hyp)
    return parsed


def import_dataset_results(
    task: TestTask,
    dataset: Dataset,
    staging_dir: Path,
    result_subdir: Path | None = None,
) -> TestTaskDataset:
    """从 K2 输出目录导入单个数据集的测试结果."""
    meta = _load_index_map(staging_dir)
    index_map: dict[str, dict[str, int]] = meta.get("index_map") or {}

    if result_subdir is None:
        result_subdir = _find_latest_result_subdir(staging_dir)
    if result_subdir is None or not result_subdir.is_dir():
        raise FileNotFoundError(f"未找到 K2 推理结果目录: {staging_dir / 'results'}")

    audio_by_id = {a.id: a for a in dataset.audios.filter(status=1)}

    results_to_create: list[TestAudioResult] = []
    total_duration = 0.0
    s_sum = i_sum = d_sum = h_sum = 0
    wer_sum = 0.0
    n_ref_sum = 0
    count = 0

    for k2_lang, idx_to_audio_id in index_map.items():
        result_key = k2_result_key(k2_lang)
        result_file = result_subdir / f"{k2_lang}_result.jsonl"
        if not result_file.is_file():
            result_file = result_subdir / f"{k2_lang.replace('-cn', '')}_result.jsonl"
        if not result_file.is_file():
            continue

        parsed = _parse_result_jsonl(result_file, result_key)
        for idx_str, audio_id in idx_to_audio_id.items():
            audio = audio_by_id.get(audio_id)
            if not audio:
                continue
            ref, hyp = parsed.get(idx_str, (audio.ref_text or "", ""))
            if not ref:
                ref = audio.ref_text or ""
            detail = compute_wer(ref, hyp)
            results_to_create.append(
                TestAudioResult(
                    task=task,
                    dataset=dataset,
                    audio=audio,
                    ref_text=ref,
                    hyp_text=hyp,
                    wer=detail["wer"],
                    errors_json=detail,
                )
            )
            total_duration += audio.duration or 0
            s_sum += detail["s_cnt"]
            i_sum += detail["i_cnt"]
            d_sum += detail["d_cnt"]
            h_sum += detail["hit_cnt"]
            n_ref_sum += detail["n_ref"]
            wer_sum += detail["wer"]
            count += 1

    if not results_to_create:
        raise ValueError(f"数据集「{dataset.name}」未能从 K2 结果中导入任何音频记录")

    with transaction.atomic():
        TestAudioResult.objects.filter(task=task, dataset=dataset).delete()
        TestAudioResult.objects.bulk_create(results_to_create)

        td, _ = TestTaskDataset.objects.get_or_create(task=task, dataset=dataset)
        td.total_audio = count
        td.total_duration = round(total_duration, 2)
        td.avg_wer = round(wer_sum / count, 4) if count else 0
        td.ret = round((s_sum + i_sum + d_sum) / n_ref_sum, 4) if n_ref_sum else 0
        td.s_cnt = s_sum
        td.i_cnt = i_sum
        td.d_cnt = d_sum
        td.hit_cnt = h_sum
        td.save()

    return td
