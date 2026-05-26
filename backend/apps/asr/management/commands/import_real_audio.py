"""扫描 others/test_datas 目录，把里面的 .wav 和同名 .txt 配对导入数据库.

执行方式:
    python manage.py import_real_audio

- 自动复制 wav 到 backend/media/audio/
- 用同名 .txt 作为 ref_text
- 用 wave 标准库读出真实时长
- 文件名前缀(zh_/en_)自动识别语种
- 同名音频已存在则更新，不会重复插入
- 同时把所有新导入的音频挂到「真实测试集」这个数据集下
"""
from __future__ import annotations

import contextlib
import shutil
import wave
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from apps.asr.models import Audio, Dataset, DatasetAudio


SOURCE_DIR = Path(settings.BASE_DIR).parent / "others" / "test_datas"


def detect_language(stem: str) -> str:
    s = stem.lower()
    for lang in ("zh", "en", "es", "ja", "ko", "ru", "fr", "de", "th", "it", "ar"):
        if s.startswith(f"{lang}_") or s == lang:
            return lang
    return "zh"


def get_wav_duration(path: Path) -> float:
    """用标准库 wave 读取 wav 时长(秒)，失败返回 0."""
    try:
        with contextlib.closing(wave.open(str(path), "rb")) as wf:
            frames = wf.getnframes()
            rate = wf.getframerate()
            if rate <= 0:
                return 0.0
            return round(frames / float(rate), 2)
    except Exception:
        return 0.0


class Command(BaseCommand):
    help = "扫描 others/test_datas 把真实 wav 导入到 audio 表 + 数据集"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dataset",
            default="真实测试集",
            help="导入后挂到的数据集名称(自动创建)，默认 真实测试集",
        )

    def handle(self, *args, **options):
        if not SOURCE_DIR.exists():
            self.stderr.write(self.style.ERROR(f"源目录不存在: {SOURCE_DIR}"))
            return

        target_dir = Path(settings.MEDIA_ROOT) / "audio"
        target_dir.mkdir(parents=True, exist_ok=True)

        ds_name = options["dataset"]
        dataset, _ = Dataset.objects.get_or_create(
            name=ds_name,
            defaults={"language": "zh"},
        )
        self.stdout.write(self.style.SUCCESS(f"目标数据集: {dataset.name} (id={dataset.id})"))

        wav_files = sorted(SOURCE_DIR.glob("*.wav"))
        if not wav_files:
            self.stdout.write(self.style.WARNING(f"在 {SOURCE_DIR} 没找到 .wav 文件"))
            return

        ok, updated = 0, 0
        for wav in wav_files:
            stem = wav.stem
            language = detect_language(stem)

            # 文本匹配优先级：
            #   1) 同名 txt：zh_guojun.wav -> zh_guojun.txt
            #   2) 前缀 txt：zh_guojun.wav -> zh.txt (按文件名第一段)
            #   3) 语种 txt：zh_guojun.wav -> zh.txt (按识别出的语种)
            candidate_txts = [
                SOURCE_DIR / f"{stem}.txt",
                SOURCE_DIR / f"{stem.split('_', 1)[0]}.txt",
                SOURCE_DIR / f"{language}.txt",
            ]
            ref_text = ""
            for txt in candidate_txts:
                if txt.exists():
                    ref_text = txt.read_text(encoding="utf-8", errors="ignore").strip()
                    break

            target_path = target_dir / wav.name
            shutil.copy2(wav, target_path)

            duration = get_wav_duration(target_path)
            url_path = f"{settings.MEDIA_URL}audio/{wav.name}"

            obj, created = Audio.objects.update_or_create(
                name=wav.name,
                defaults={
                    "language": language,
                    "audio_path": url_path,
                    "source": "outside",
                    "noise": "quiet",
                    "industry": "unknown",
                    "duration": duration,
                    "ref_text": ref_text,
                    "status": 1,
                },
            )

            DatasetAudio.objects.get_or_create(audio=obj, dataset=dataset)

            if created:
                ok += 1
            else:
                updated += 1

            self.stdout.write(
                f"  - {wav.name:30s}  lang={language}  duration={duration:>7.2f}s  "
                f"text_len={len(ref_text):>6d}  {'NEW' if created else 'UPDATED'}"
            )

        self.stdout.write(self.style.SUCCESS(
            f"[OK] 新增 {ok} 条，更新 {updated} 条，全部挂到《{dataset.name}》"
        ))
