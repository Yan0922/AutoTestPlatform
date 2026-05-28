"""远程模型下载后台任务（Celery + Redis 进度存储）."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from .redis_job_store import get_job, get_job_status, has_running_job, save_job, update_job


def _now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _is_cancelled(job_id: str) -> bool:
    job = get_job(job_id)
    return bool(job and job.get("cancel_requested"))


def start_remote_download_job(languages: list[str], sizes: list[str], versions: list[str]) -> str:
    combos: list[tuple[str, str, str]] = []
    for language in languages:
        for size in sizes:
            for version in versions:
                combos.append((language, size, version))

    if not combos:
        raise ValueError("languages / sizes / versions 均为必填")

    if has_running_job():
        raise ValueError("已有下载任务正在进行，请等待完成或先取消")

    job_id = str(uuid.uuid4())
    job = {
        "job_id": job_id,
        "status": "running",
        "cancel_requested": False,
        "total_items": len(combos),
        "current_item_index": 0,
        "current_item": None,
        "phase": "pending",
        "phase_label": "准备中",
        "percent": 0,
        "downloaded_bytes": 0,
        "total_bytes": None,
        "message": "任务已启动",
        "ok": 0,
        "skipped": 0,
        "failed": 0,
        "results": [],
        "started_at": _now_str(),
        "finished_at": None,
        "error": None,
    }
    save_job(job)

    from .celery_tasks import dispatch_celery_task, run_remote_download_task

    dispatch_celery_task(run_remote_download_task, job_id, languages, sizes, versions)
    return job_id


def cancel_remote_download_job(job_id: str) -> bool:
    job = get_job(job_id)
    if not job:
        return False
    if job["status"] != "running":
        return False
    # 立即标记为已取消，避免无 Worker 时进度条一直卡在 running
    update_job(
        job_id,
        cancel_requested=True,
        status="cancelled",
        phase="done",
        phase_label="已取消",
        finished_at=_now_str(),
        message="下载已取消",
    )
    return True


def run_download_job(
    job_id: str,
    languages: list[str],
    sizes: list[str],
    versions: list[str],
) -> None:
    """Celery worker 内执行的实际下载逻辑."""
    job = get_job(job_id)
    if not job:
        return

    combos: list[tuple[str, str, str]] = []
    for language in languages:
        for size in sizes:
            for version in versions:
                combos.append((language, size, version))
    total = len(combos)

    def cancel_check() -> bool:
        return _is_cancelled(job_id)

    def on_progress(payload: dict[str, Any]) -> None:
        item_index = payload.get("item_index", 0)
        item_fraction = float(payload.get("item_fraction", 0))
        overall = int(((item_index + item_fraction) / total) * 100) if total else 0
        overall = min(99, max(0, overall))
        update_job(
            job_id,
            current_item_index=item_index + 1,
            current_item=payload.get("current_item"),
            phase=payload.get("phase"),
            phase_label=payload.get("phase_label"),
            percent=overall,
            downloaded_bytes=payload.get("downloaded_bytes", 0),
            total_bytes=payload.get("total_bytes"),
            message=payload.get("message", ""),
        )

    try:
        result = download_models_batch(
            languages,
            sizes,
            versions,
            cancel_check=cancel_check,
            on_progress=on_progress,
        )
        status = "cancelled" if cancel_check() else "completed"
        last_job = get_job(job_id) or {}
        last_percent = last_job.get("percent", 0)
        update_job(
            job_id,
            status=status,
            percent=100 if status == "completed" else last_percent,
            phase="done",
            phase_label="已取消" if status == "cancelled" else "完成",
            ok=result.get("ok", 0),
            skipped=result.get("skipped", 0),
            failed=result.get("failed", 0),
            results=result.get("results", []),
            finished_at=_now_str(),
            message="下载已取消" if status == "cancelled" else "全部处理完成",
        )
    except DownloadCancelled:
        update_job(
            job_id,
            status="cancelled",
            phase="done",
            phase_label="已取消",
            finished_at=_now_str(),
            message="下载已取消",
        )
    except Exception as exc:  # noqa: BLE001
        update_job(
            job_id,
            status="failed",
            phase="error",
            phase_label="失败",
            finished_at=_now_str(),
            error=str(exc),
            message=str(exc),
        )
