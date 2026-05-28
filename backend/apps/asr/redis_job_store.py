"""远程下载任务进度存储（Redis 优先，不可用时回退进程内内存）."""
from __future__ import annotations

import json
import logging
import threading
from copy import deepcopy
from typing import Any

from django.conf import settings

logger = logging.getLogger(__name__)

JOB_KEY_PREFIX = "asr:download:job:"
CURRENT_JOB_KEY = "asr:download:current"
JOB_TTL_SECONDS = 7 * 86400

_lock = threading.Lock()
_memory_jobs: dict[str, dict[str, Any]] = {}
_memory_current_job_id: str | None = None
_redis_client = None
_redis_available: bool | None = None


def _get_redis():
    global _redis_client, _redis_available
    if _redis_available is False:
        return None
    if _redis_client is not None:
        return _redis_client
    try:
        import redis

        _redis_client = redis.from_url(settings.CELERY_BROKER_URL, decode_responses=True)
        _redis_client.ping()
        _redis_available = True
        return _redis_client
    except Exception as exc:  # noqa: BLE001
        logger.warning("Redis 不可用，下载进度使用进程内内存: %s", exc)
        _redis_available = False
        return None


def _job_key(job_id: str) -> str:
    return f"{JOB_KEY_PREFIX}{job_id}"


def save_job(job: dict[str, Any]) -> None:
    job_id = job["job_id"]
    client = _get_redis()
    if client:
        payload = json.dumps(job, ensure_ascii=False)
        client.set(_job_key(job_id), payload, ex=JOB_TTL_SECONDS)
        if job.get("status") == "running":
            client.set(CURRENT_JOB_KEY, job_id, ex=JOB_TTL_SECONDS)
        return

    with _lock:
        global _memory_current_job_id
        _memory_jobs[job_id] = deepcopy(job)
        if job.get("status") == "running":
            _memory_current_job_id = job_id


def get_job(job_id: str) -> dict[str, Any] | None:
    client = _get_redis()
    if client:
        raw = client.get(_job_key(job_id))
        if not raw:
            return None
        return json.loads(raw)

    with _lock:
        job = _memory_jobs.get(job_id)
        return deepcopy(job) if job else None


def get_current_job_id() -> str | None:
    client = _get_redis()
    if client:
        return client.get(CURRENT_JOB_KEY)

    with _lock:
        return _memory_current_job_id


def get_job_status(job_id: str | None = None) -> dict[str, Any] | None:
    if job_id:
        return get_job(job_id)
    current = get_current_job_id()
    if current:
        return get_job(current)
    return None


def update_job(job_id: str, **fields: Any) -> None:
    job = get_job(job_id)
    if not job:
        return
    job.update(fields)
    save_job(job)
    if fields.get("status") in ("completed", "cancelled", "failed"):
        client = _get_redis()
        if client:
            current = client.get(CURRENT_JOB_KEY)
            if current == job_id:
                client.delete(CURRENT_JOB_KEY)
        else:
            with _lock:
                global _memory_current_job_id
                if _memory_current_job_id == job_id:
                    _memory_current_job_id = None


def has_running_job() -> bool:
    current = get_current_job_id()
    if not current:
        return False
    job = get_job(current)
    return bool(job and job.get("status") == "running")
