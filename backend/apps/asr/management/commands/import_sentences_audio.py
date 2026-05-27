"""从 sentences.jsonl 导入真实音频（已合并到 import_media_audio，本命令保留兼容）."""
from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "兼容入口：等价于 import_media_audio --replace-fake"

    def add_arguments(self, parser):
        parser.add_argument("--dataset", default="真实测试集")
        parser.add_argument(
            "--replace-fake",
            action="store_true",
            help="软删除 seed_demo 假数据",
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING(
            "import_sentences_audio 已合并到 import_media_audio，正在转发执行…"
        ))
        kwargs = {"dataset": options["dataset"]}
        if options["replace_fake"]:
            kwargs["replace_fake"] = True
        call_command("import_media_audio", **kwargs)
