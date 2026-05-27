"""扫描 media/audio 根目录下的 loose wav 导入（legacy；新数据请用 import_media_audio）."""
from __future__ import annotations

import contextlib
import wave
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from apps.asr.models import Audio, Dataset, DatasetAudio

MEDIA_AUDIO = Path(settings.MEDIA_ROOT) / "audio"


def detect_language(stem: str) -> str:
    s = stem.lower()
    for lang in ("zh", "en", "es", "ja", "ko", "ru", "fr", "de", "th", "it", "ar"):
        if s.startswith(f"{lang}_") or s == lang:
            return lang
    return "zh"


def get_wav_duration(path: Path) -> float:
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
    help = "扫描 media/audio/ 根目录下的 .wav（不含语种子目录）并导入数据库"

    def add_arguments(self, parser):
        parser.add_argument("--dataset", default="真实测试集")

    def handle(self, *args, **options):
        if not MEDIA_AUDIO.is_dir():
            self.stderr.write(self.style.ERROR(f"目录不存在: {MEDIA_AUDIO}"))
            return

        dataset, _ = Dataset.objects.get_or_create(
            name=options["dataset"],
            defaults={"language": "zh"},
        )

        wav_files = sorted(MEDIA_AUDIO.glob("*.wav"))
        if not wav_files:
            self.stdout.write(self.style.WARNING(
                f"{MEDIA_AUDIO} 根目录无 loose wav；语种子目录请用 import_media_audio"
            ))
            return

        ok, updated = 0, 0
        for wav in wav_files:
            stem = wav.stem
            language = detect_language(stem)
            ref_text = ""
            for txt in (MEDIA_AUDIO / f"{stem}.txt", MEDIA_AUDIO / f"{language}.txt"):
                if txt.is_file():
                    ref_text = txt.read_text(encoding="utf-8", errors="ignore").strip()
                    break

            duration = get_wav_duration(wav)
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
            ok += int(created)
            updated += int(not created)

        self.stdout.write(self.style.SUCCESS(
            f"[OK] 新增 {ok} 条，更新 {updated} 条"
        ))
