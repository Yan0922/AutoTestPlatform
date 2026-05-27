"""为指定任务/数据集生成 K2 scp/src staging 目录（不执行推理，便于本地验证）."""
from django.core.management.base import BaseCommand

from apps.asr.k2_engine.scp_src_builder import build_scp_src_for_dataset
from apps.asr.models import Dataset, TestTask


class Command(BaseCommand):
    help = "从数据池数据集生成 K2 测试用 scp/src 文件"

    def add_arguments(self, parser):
        parser.add_argument("--task-id", type=int, required=True, help="测试任务 ID")
        parser.add_argument("--dataset-id", type=int, help="仅生成指定数据集；缺省则生成任务下全部数据集")

    def handle(self, *args, **options):
        task_id = options["task_id"]
        dataset_id = options.get("dataset_id")

        task = TestTask.objects.get(id=task_id)
        qs = task.task_datasets.select_related("dataset")
        if dataset_id:
            qs = qs.filter(dataset_id=dataset_id)

        for td in qs:
            dataset = td.dataset
            audios = list(dataset.audios.filter(status=1).order_by("id"))
            staging_dir, langs = build_scp_src_for_dataset(task.name, task.id, dataset, audios)
            self.stdout.write(self.style.SUCCESS(
                f"数据集「{dataset.name}」: {staging_dir}  语种={langs}  音频数={len(audios)}"
            ))
