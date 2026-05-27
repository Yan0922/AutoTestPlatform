"""调用 model-test 脚本执行 K2 批量推理与 WER 评估."""

from __future__ import annotations



from datetime import datetime

from pathlib import Path



from django.conf import settings



from ..models import TestTask



from .config import ensure_k2_on_path, is_k2_available

from .result_importer import import_dataset_results

from .scp_src_builder import build_scp_src_for_dataset

from .single_infer import k2_langs_for_model, resolve_testasr_model_path, run_single_model_on_staging





def _collect_audios(dataset):

    return list(dataset.audios.filter(status=1).order_by("id"))





def execute_k2_test_task(task_id: int) -> None:

    """使用 K2 testAsr 对任务选中的单个模型执行推理（不扫描 models/asr 下全部模型）."""

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



        model_path = resolve_testasr_model_path(task.model)

        task_datasets = list(task.task_datasets.select_related("dataset").all())

        if not task_datasets:

            raise ValueError("任务未关联任何数据集")



        for td in task_datasets:

            dataset = td.dataset

            audios = _collect_audios(dataset)

            if not audios:

                raise ValueError(f"数据集「{dataset.name}」没有可用音频")



            staging_dir, lang_list = build_scp_src_for_dataset(task.name, task.id, dataset, audios)

            result_root = staging_dir / "results"

            result_root.mkdir(parents=True, exist_ok=True)



            run_langs = k2_langs_for_model(task.model, lang_list)

            run_single_model_on_staging(model_path, staging_dir, result_root, run_langs)



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


