"""将历史「重新运行」产生的任务关联到根任务，列表只展示根任务."""
from django.db import migrations


def _dataset_ids(task, TestTaskDataset):
    return sorted(
        TestTaskDataset.objects.filter(task_id=task.id).values_list("dataset_id", flat=True)
    )


def _base_name(name: str) -> str:
    import re

    name = (name or "").strip()
    m = re.search(r"_\d{8}_\d{4}$", name)
    if m:
        base = name[: m.start()].strip()
        return base or "task"
    return name or "task"


def backfill_root_tasks(apps, schema_editor):
    TestTask = apps.get_model("asr", "TestTask")
    TestTaskDataset = apps.get_model("asr", "TestTaskDataset")

    tasks = list(
        TestTask.objects.filter(status=1, root_task_id__isnull=True).order_by("created_at", "id")
    )
    buckets: dict[tuple, list] = {}
    for task in tasks:
        key = (task.model_id, _base_name(task.name), tuple(_dataset_ids(task, TestTaskDataset)))
        buckets.setdefault(key, []).append(task)

    for group in buckets.values():
        if len(group) <= 1:
            continue
        root = group[0]
        for derived in group[1:]:
            if derived.root_task_id is None:
                derived.root_task_id = root.id
                derived.save(update_fields=["root_task_id"])


class Migration(migrations.Migration):

    dependencies = [
        ("asr", "0002_testtask_root_task"),
    ]

    operations = [
        migrations.RunPython(backfill_root_tasks, migrations.RunPython.noop),
    ]
