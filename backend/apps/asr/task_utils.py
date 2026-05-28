"""测试任务名称工具."""
from __future__ import annotations

import re
from datetime import datetime

_TASK_NAME_SUFFIX_RE = re.compile(r"_\d{8}_\d{4}$")


def task_name_suffix(when: datetime | None = None) -> str:
    """时间后缀，例如 _20260527_1438."""
    when = when or datetime.now()
    return when.strftime("_%Y%m%d_%H%M")


def build_task_name(raw_name: str, when: datetime | None = None) -> str:
    """
    将用户输入的任务名与运行时间拼接。

    示例: test + 2026-05-27 14:38 → test_20260527_1438
    总长度不超过 30（与数据库字段一致）。
    """
    suffix = task_name_suffix(when)
    base = (raw_name or "task").strip() or "task"
    max_base_len = max(1, 30 - len(suffix))
    return f"{base[:max_base_len]}{suffix}"


def extract_task_base_name(task_name: str) -> str:
    """从带时间后缀的任务名还原用户输入的前缀，例如 test_20260527_1438 → test."""
    name = (task_name or "").strip()
    if _TASK_NAME_SUFFIX_RE.search(name):
        base = _TASK_NAME_SUFFIX_RE.sub("", name).strip()
        return base or "task"
    return name or "task"
