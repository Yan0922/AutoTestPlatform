"""Celery 后台任务（ASR 测试推理、远程模型下载）."""
from __future__ import annotations

import logging

from celery import shared_task
from django.db import connection

logger = logging.getLogger(__name__)


def execute_test_task_worker(task_id: int) -> None:
    from apps.asr.tasks import execute_test_task

    execute_test_task(task_id)


def execute_remote_download_worker(
    job_id: str,
    languages: list[str],
    sizes: list[str],
    versions: list[str],
) -> None:
    from apps.asr.remote_download_job import run_download_job

    run_download_job(job_id, languages, sizes, versions)


@shared_task(
    bind=True,
    name="asr.run_test_task",
    ignore_result=True,
    soft_time_limit=7200,
    time_limit=7260,
)
def run_test_task(self, task_id: int) -> None:
    """执行 ASR 测试任务（K2 或模拟）."""
    try:
        execute_test_task_worker(task_id)
    finally:
        connection.close()


@shared_task(
    bind=True,
    name="asr.run_remote_download",
    ignore_result=True,
    soft_time_limit=86400,
    time_limit=86460,
)
def run_remote_download_task(
    self,
    job_id: str,
    languages: list[str],
    sizes: list[str],
    versions: list[str],
) -> None:
    """后台下载远程 ASR 模型."""
    try:
        execute_remote_download_worker(job_id, languages, sizes, versions)
    finally:
        connection.close()


def dispatch_celery_task(task, *args, **kwargs):
    """
    派发 Celery 任务。

    CELERY_TASK_ALWAYS_EAGER=1 且无 worker 时，用线程异步执行，避免阻塞 HTTP。
    生产环境应设 CELERY_TASK_ALWAYS_EAGER=0 并单独启动 celery worker。
    broker 不可用时自动回退线程，避免创建任务直接失败。
    """
    from django.conf import settings

    def _run_in_thread() -> None:
        import threading

        def _run() -> None:
            try:
                task.run(*args, **kwargs)
            finally:
                connection.close()

        threading.Thread(target=_run, daemon=True).start()

    if getattr(settings, "CELERY_TASK_ALWAYS_EAGER", False):
        _run_in_thread()
        return None

    try:
        return task.delay(*args, **kwargs)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Celery broker 不可用，回退线程执行: %s", exc)
        _run_in_thread()
        return None
