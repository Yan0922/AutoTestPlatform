"""单模型 K2 推理：只跑任务选中的那一个模型，不扫描整个目录."""
from __future__ import annotations

import time
from pathlib import Path

from django.conf import settings

from ..models import AsrModel

from .lang_mapping import k2_scp_filename, k2_src_filename, platform_lang_to_k2_scp_lang


def resolve_testasr_model_path(model: AsrModel) -> Path:
    """
    返回 testAsr 可直接使用的模型目录（含 *.onnx 的那一层）。

    平台每个模型对应 media/models/asr/{name}/，例如 zh_base_v1.0.0.6/
    """
    if not model.dir_path:
        raise ValueError(f"模型「{model.name}」未配置 dir_path")
    model_dir = (Path(settings.MEDIA_ROOT) / model.dir_path).resolve()
    if not model_dir.is_dir():
        raise FileNotFoundError(f"模型目录不存在: {model_dir}")

    if list(model_dir.glob("*.onnx")) or (model_dir / "tokens.txt").is_file():
        return model_dir

    candidates = [c for c in model_dir.iterdir() if c.is_dir() and "_v" in c.name]
    if len(candidates) == 1:
        return candidates[0]
    if model.name:
        by_name = model_dir / model.name
        if by_name.is_dir() and (list(by_name.glob("*.onnx")) or (by_name / "tokens.txt").is_file()):
            return by_name

    raise ValueError(
        f"模型「{model.name}」目录中未找到可用的 onnx 模型文件: {model_dir}"
    )


def k2_langs_for_model(model: AsrModel, staging_langs: list[str]) -> list[str]:
    """只跑与所选模型语种匹配的 scp."""
    model_lang = platform_lang_to_k2_scp_lang(model.language)
    if model_lang in staging_langs:
        return [model_lang]
    return staging_langs


def run_single_model_on_staging(
    model_path: Path,
    staging_dir: Path,
    result_root: Path,
    k2_langs: list[str],
) -> Path:
    """
    对单个模型 + staging 目录执行 testAsr 推理与 WER。

    复用 model-test 中的函数，不调用 infer_batch_all，不修改原脚本。
    """
    from k2_asr_model_test.asr_test_code.test_cases.test_batch_infer import (  # noqa: WPS433
        infer_batch_lang,
        save_predict_result_as_jsonl,
    )
    from k2_asr_model_test.asr_test_code.utils.comm import k2_model_update_json_reference  # noqa: WPS433
    from k2_asr_model_test.asr_test_code.utils.new_wer_eval import get_wer  # noqa: WPS433

    save_dir = result_root / f"{staging_dir.name}_{time.strftime('%Y%m%d_%H%M%S')}"
    save_dir.mkdir(parents=True, exist_ok=True)

    for k2_lang in k2_langs:
        scp_file = staging_dir / k2_scp_filename(k2_lang)
        if not scp_file.is_file():
            continue

        result = infer_batch_lang(str(model_path), str(scp_file))
        jsonl_lang = "zh-cn" if k2_lang == "zh-cn" else k2_lang
        jsonl_path = save_dir / f"{jsonl_lang}.jsonl"
        save_predict_result_as_jsonl(result, jsonl_lang, str(jsonl_path))

        src_file = staging_dir / k2_src_filename(k2_lang)
        if src_file.is_file() and jsonl_path.is_file():
            k2_model_update_json_reference(str(jsonl_path), str(src_file))
            result_jsonl = save_dir / f"{jsonl_lang}_result.jsonl"
            if result_jsonl.is_file():
                get_wer(str(result_jsonl), transcription_key=jsonl_lang)

    return save_dir
