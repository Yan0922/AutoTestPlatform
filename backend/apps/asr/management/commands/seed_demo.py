"""一键生成演示数据."""
import random

from django.core.management.base import BaseCommand

from apps.asr.models import (
    Audio,
    AsrModel,
    Dataset,
    DatasetAudio,
)

DEMO_TEXTS = [
    "今天天气真不错适合出去散步",
    "人工智能正在改变我们的生活方式",
    "请把音量调到适中的位置",
    "明天上午十点我们开个线上会议",
    "深度学习模型在不断进步",
    "语音识别准确率越来越高",
    "我们要持续优化数据质量",
    "请确认订单后再点击提交按钮",
]


class Command(BaseCommand):
    help = "生成演示用模型/数据集/音频数据"

    def handle(self, *args, **options):
        if not AsrModel.objects.exists():
            AsrModel.objects.create(name="ASR-中文通用-Base", language="zh", version="v1.0", size="base", dir_path="models/asr/demo")
            AsrModel.objects.create(name="ASR-英文-Small", language="en", version="v0.9", size="small", dir_path="models/asr/demo2")
            self.stdout.write(self.style.SUCCESS("已生成 2 个示例模型"))

        ds1, _ = Dataset.objects.get_or_create(name="日常对话集", defaults={"language": "zh"})
        ds2, _ = Dataset.objects.get_or_create(name="科技新闻集", defaults={"language": "zh"})

        if Audio.objects.count() < 10:
            for i in range(20):
                a = Audio.objects.create(
                    name=f"demo_{i:03d}.wav",
                    language="zh",
                    audio_path="/media/audio/demo.wav",
                    source=random.choice(["Sota1", "Sota2", "gf", "outside"]),
                    noise=random.choice(["quiet", "low_mid", "mid_high"]),
                    industry=random.choice(["technology", "economy", "unknown"]),
                    duration=round(random.uniform(1.5, 8.0), 2),
                    ref_text=random.choice(DEMO_TEXTS),
                )
                DatasetAudio.objects.get_or_create(audio=a, dataset=random.choice([ds1, ds2]))
            self.stdout.write(self.style.SUCCESS("已生成 20 条示例音频"))
        self.stdout.write(self.style.SUCCESS("演示数据准备完毕!"))
