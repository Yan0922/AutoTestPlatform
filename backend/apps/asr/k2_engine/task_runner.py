"""调用 model-test 脚本执行 K2 批量推理与 WER 评估."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

from django.conf import settings

from ..models import TestTask

from .config import ensure_k2_on_path, is_k2_available, k2_pro_dpath
from .result_importer import import_dataset_results
from .scp_src_builder import build_scp_src_for_dataset


def _collect_audios(dataset):
    return list(dataset.audios.filter(status=1).order_by("id"))


def _resolve_model_dir(task: TestTask) -> Path:
    model = task.model
    if not model.dir_path:
        raise ValueError(f"模型「{model.name}」未配置 dir_path")
    model_dir = Path(settings.MEDIA_ROOT) / model.dir_path
    if not model_dir.is_dir():
        raise FileNotFoundError(f"模型目录不存在: {model_dir}")
    return model_dir


def execute_k2_test_task(task_id: int) -> None:
    """使用 K2 testAsr 流水线执行测试任务（不修改 model-test 原脚本）."""
    if not is_k2_available():
        raise RuntimeError(
            "K2 引擎不可用：请设置 K2_ENGINE_ENABLED=1，并确保 TESTASR_BIN 或 k2_asr_model_test/testAsr 存在"
        )

    try:
        task = TestTask.objects.select_related("model").get(id=task_id)
    except TestTask.DoesNotExist:
        return

    try:
        ensure_k2_on_path()
        pro_dpath = k2_pro_dpath()
        if not pro_dpath:
            raise RuntimeError("找不到 k2_asr_model_test 目录")

        from k2_asr_model_test.asr_test_code.test_cases.test_cases_mutil_thread import (  # noqa: WPS433
            case_test_one_datases_all_lang,
        )
        model_dir = _resolve_model_dir(task)
        task_datasets = list(task.task_datasets.select_related("dataset").all())
        if not task_datasets:
            raise ValueError("任务未关联任何数据集")

        for td in task_datasets:
            dataset = td.dataset
            audios = _collect_audios(dataset)
            if not audios:
                raise ValueError(f"数据集「{dataset.name}」没有可用音频")

            staging_dir, lang_list = build_scp_src_for_dataset(task.id, dataset, audios)
            result_root = staging_dir / "results"
            result_root.mkdir(parents=True, exist_ok=True)

            # infer_batch_all 内部 os.chdir(PRO_DPATH)，需保证 testAsr 在该目录
            case_test_one_datases_all_lang(
                str(model_dir),
                str(staging_dir),
                str(result_root),
                lang_list=lang_list,
            )

            import_dataset_results(task, dataset, staging_dir)

        task.task_status = 2
        task.finished_at = datetime.now()
        task.error_message = ""
        task.save(update_fields=["task_status", "finished_at", "error_message"])
    except Exception as exc:  # noqa: BLE001
        task.task_status = 3
        task.error_message = str(exc)
        task.finished_at = datetime.now()
        task.save(update_fields=["task_status", "finished_at", "error_message"])
