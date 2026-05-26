"""远程模型下载后台任务与进度（内存存储，单进程开发/部署）."""
from __future__ import annotations

import threading
import uuid
from copy import deepcopy
from datetime import datetime
from typing import Any, Callable

from .remote_model import DownloadCancelled, download_models_batch

_lock = threading.Lock()
_jobs: dict[str, dict[str, Any]] = {}
_current_job_id: str | None = None


def _now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _snapshot(job: dict[str, Any]) -> dict[str, Any]:
    return deepcopy(job)


def get_job_status(job_id: str | None = None) -> dict[str, Any] | None:
    with _lock:
        if job_id:
            job = _jobs.get(job_id)
            return _snapshot(job) if job else None
        if _current_job_id and _current_job_id in _jobs:
            return _snapshot(_jobs[_current_job_id])
        return None


def _update_job(job_id: str, **fields: Any) -> None:
    with _lock:
        job = _jobs.get(job_id)
        if not job:
            return
        job.update(fields)


def _is_cancelled(job_id: str) -> bool:
    with _lock:
        job = _jobs.get(job_id)
        return bool(job and job.get("cancel_requested"))


def start_remote_download_job(languages: list[str], sizes: list[str], versions: list[str]) -> str:
    combos: list[tuple[str, str, str]] = []
    for language in languages:
        for size in sizes:
            for version in versions:
                combos.append((language, size, version))

    if not combos:
        raise ValueError("languages / sizes / versions 均为必填")

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

    with _lock:
        global _current_job_id
        if _current_job_id and _jobs.get(_current_job_id, {}).get("status") == "running":
            raise ValueError("已有下载任务正在进行，请等待完成或先取消")
        _jobs[job_id] = job
        _current_job_id = job_id

    thread = threading.Thread(
        target=_run_job,
        args=(job_id, languages, sizes, versions, combos),
        daemon=True,
    )
    thread.start()
    return job_id


def cancel_remote_download_job(job_id: str) -> bool:
    with _lock:
        job = _jobs.get(job_id)
        if not job:
            return False
        if job["status"] != "running":
            return False
        job["cancel_requested"] = True
        job["message"] = "正在取消…"
        return True


def _run_job(
    job_id: str,
    languages: list[str],
    sizes: list[str],
    versions: list[str],
    combos: list[tuple[str, str, str]],
) -> None:
    total = len(combos)

    def cancel_check() -> bool:
        return _is_cancelled(job_id)

    def on_progress(payload: dict[str, Any]) -> None:
        item_index = payload.get("item_index", 0)
        item_fraction = float(payload.get("item_fraction", 0))
        overall = int(((item_index + item_fraction) / total) * 100) if total else 0
        overall = min(99, max(0, overall))
        _update_job(
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
        with _lock:
            last_percent = _jobs.get(job_id, {}).get("percent", 0)
        _update_job(
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
        _update_job(
            job_id,
            status="cancelled",
            phase="done",
            phase_label="已取消",
            finished_at=_now_str(),
            message="下载已取消",
        )
    except Exception as exc:  # noqa: BLE001
        _update_job(
            job_id,
            status="failed",
            phase="error",
            phase_label="失败",
            finished_at=_now_str(),
            error=str(exc),
            message=str(exc),
        )
