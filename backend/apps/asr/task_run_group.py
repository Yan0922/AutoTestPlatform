"""测试任务「重新运行」同组任务查询."""
from __future__ import annotations

from django.db.models import Q
from django.utils import timezone

from .models import TestTask
from .task_utils import extract_task_base_name

_CN_ORDINALS = ("一", "二", "三", "四", "五", "六", "七", "八", "九", "十")

# 列表展示用（非数据库 task_status）
LIST_STATUS_RERUNNING = 4


def run_group_label(index: int) -> str:
    """1-based index → 第一次运行结果."""
    if 1 <= index <= len(_CN_ORDINALS):
        return f"第{_CN_ORDINALS[index - 1]}次运行结果"
    return f"第{index}次运行结果"


def _dataset_ids(task: TestTask) -> list[int]:
    return sorted(task.task_datasets.values_list("dataset_id", flat=True))


def _find_by_config_fallback(task: TestTask) -> list[TestTask]:
    """兼容未写入 root_task 的历史任务：同模型、同数据集、同名称前缀."""
    base = extract_task_base_name(task.name)
    dataset_ids = _dataset_ids(task)
    if not dataset_ids:
        return [task]

    candidates = (
        TestTask.objects.filter(status=1, model_id=task.model_id)
        .prefetch_related("task_datasets")
        .order_by("created_at", "id")
    )
    related: list[TestTask] = []
    for candidate in candidates:
        if extract_task_base_name(candidate.name) != base:
            continue
        if _dataset_ids(candidate) == dataset_ids:
            related.append(candidate)
    return related or [task]


def get_run_group_tasks(task: TestTask) -> list[TestTask]:
    """返回同一「重新运行」链上的全部任务，按创建时间升序."""
    root_id = task.root_task_id
    if root_id:
        qs = (
            TestTask.objects.filter(status=1)
            .filter(Q(pk=root_id) | Q(root_task_id=root_id))
            .order_by("created_at", "id")
        )
        return list(qs)

    if task.derived_runs.filter(status=1).exists():
        qs = (
            TestTask.objects.filter(status=1)
            .filter(Q(pk=task.pk) | Q(root_task_id=task.pk))
            .order_by("created_at", "id")
        )
        return list(qs)

    return _find_by_config_fallback(task)


def get_run_group_root(task: TestTask) -> TestTask:
    group = get_run_group_tasks(task)
    return group[0]


def resolve_run_task(task: TestTask, run_id: int | None = None) -> TestTask:
    """解析当前应展示的运行记录；默认取最新一次."""
    group = get_run_group_tasks(task)
    if run_id is not None:
        for item in group:
            if item.id == run_id:
                return item
    return group[-1]


def get_list_display_status(root_task: TestTask) -> tuple[int, str]:
    """列表行状态：重新运行中 / 进行中 / 运行完成 / 失败."""
    group = get_run_group_tasks(root_task)
    latest = group[-1]
    if latest.task_status == 1:
        if len(group) > 1:
            return LIST_STATUS_RERUNNING, "重新运行中"
        return 1, "进行中"
    if latest.task_status == 2:
        return 2, "运行完成"
    return 3, "失败"


def group_has_running_rerun(root_task: TestTask) -> bool:
    status, _ = get_list_display_status(root_task)
    return status == LIST_STATUS_RERUNNING


def _format_dt(dt) -> str:
    if dt is None:
        return ""
    if timezone.is_aware(dt):
        dt = timezone.localtime(dt)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def serialize_run_group(task: TestTask, current_run_id: int | None = None) -> list[dict]:
    """序列化运行组导航；多次重新运行时返回各次入口."""
    group = get_run_group_tasks(task)
    root = group[0]
    if len(group) <= 1:
        return []

    if current_run_id is None:
        current_run_id = group[-1].id

    return [
        {
            "id": item.id,
            "root_id": root.id,
            "name": item.name,
            "index": idx,
            "label": run_group_label(idx),
            "started_at": _format_dt(item.created_at),
            "task_status": item.task_status,
            "is_current": item.id == current_run_id,
        }
        for idx, item in enumerate(group, start=1)
    ]
