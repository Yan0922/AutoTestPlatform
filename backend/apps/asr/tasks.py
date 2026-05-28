"""测试任务执行逻辑.



- K2 引擎可用时：从数据池生成 scp/src，调用 model-test 脚本推理并回填结果

- 否则：使用模拟推理（本地开发 / Windows 环境）

"""

from __future__ import annotations



import random

from datetime import datetime



from django.db import transaction



from .k2_engine.config import is_k2_available, is_k2_python_ready, k2_enabled

from .models import (

    Audio,

    Dataset,

    TestAudioResult,

    TestTask,

    TestTaskDataset,

)

from .wer import compute_wer





def run_asr_infer(audio: Audio, model) -> str:

    """模拟 ASR 推理 - K2 不可用时使用."""

    text = audio.ref_text or ""

    if not text:

        return ""

    chars = list(text)

    if not chars:

        return ""

    err_rate = {"base": 0.15, "small": 0.10, "large": 0.05}.get(model.size, 0.10)

    rng = random.Random(audio.id * 7919 + model.id)

    out = []

    for ch in chars:

        r = rng.random()

        if r < err_rate / 3:

            continue

        if r < err_rate * 2 / 3:

            out.append(ch)

            out.append(rng.choice(["啊", "嗯", "呃"]))

            continue

        if r < err_rate:

            out.append(rng.choice(["的", "了", "是", "在", "和"]))

            continue

        out.append(ch)

    return "".join(out)





def _collect_audios(dataset: Dataset) -> list:

    return list(dataset.audios.filter(status=1))





def execute_mock_test_task(task_id: int) -> None:

    """模拟推理流程（原有逻辑）."""

    try:

        task = TestTask.objects.select_related("model").get(id=task_id)

    except TestTask.DoesNotExist:

        return



    try:

        with transaction.atomic():

            for td in task.task_datasets.select_related("dataset").all():

                audios = _collect_audios(td.dataset)

                total_audio = len(audios)

                total_duration = 0.0

                s_sum = i_sum = d_sum = h_sum = 0

                n_ref_sum = 0

                wer_sum = 0.0



                results_to_create = []

                for audio in audios:

                    hyp = run_asr_infer(audio, task.model)

                    detail = compute_wer(audio.ref_text or "", hyp)

                    results_to_create.append(

                        TestAudioResult(

                            task=task,

                            dataset=td.dataset,

                            audio=audio,

                            ref_text=audio.ref_text or "",

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



                TestAudioResult.objects.filter(task=task, dataset=td.dataset).delete()

                TestAudioResult.objects.bulk_create(results_to_create)



                avg_wer = round(wer_sum / total_audio, 4) if total_audio else 0

                ret = round((s_sum + i_sum + d_sum) / n_ref_sum, 4) if n_ref_sum else 0

                td.total_audio = total_audio

                td.total_duration = round(total_duration, 2)

                td.avg_wer = avg_wer

                td.ret = ret

                td.s_cnt = s_sum

                td.i_cnt = i_sum

                td.d_cnt = d_sum

                td.hit_cnt = h_sum

                td.save()



            task.task_status = 2

            task.finished_at = datetime.now()

            task.error_message = ""

            task.save(update_fields=["task_status", "finished_at", "error_message"])

    except Exception as exc:  # noqa: BLE001

        task.task_status = 3

        task.error_message = str(exc)

        task.finished_at = datetime.now()

        task.save(update_fields=["task_status", "finished_at", "error_message"])





def execute_test_task(task_id: int) -> None:
    """执行测试任务：优先 K2 真实引擎，否则模拟."""
    if k2_enabled() and is_k2_available():
        from .k2_engine.task_runner import execute_k2_test_task

        execute_k2_test_task(task_id)
        return

    if k2_enabled() and not is_k2_python_ready():
        _fail_task_missing_k2_deps(task_id)
        return

    execute_mock_test_task(task_id)


def _fail_task_missing_k2_deps(task_id: int) -> None:
    msg = (
        "K2 已启用但缺少 Python 依赖（jiwer 等）。"
        "请在 backend 目录执行: pip install -r requirements-k2.txt"
    )
    try:
        task = TestTask.objects.get(id=task_id)
    except TestTask.DoesNotExist:
        return
    task.task_status = 3
    task.error_message = msg
    task.finished_at = datetime.now()
    task.save(update_fields=["task_status", "finished_at", "error_message"])


def start_test_task_async(task_id: int) -> None:
    """派发 Celery 后台任务执行测试（K2 或模拟）."""
    from .celery_tasks import dispatch_celery_task, run_test_task

    dispatch_celery_task(run_test_task, task_id)
