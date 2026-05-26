"""从 sentences.jsonl + wav 目录导入真实音频，并可选清理假数据.

执行:
    python manage.py import_sentences_audio --replace-fake

目录结构:
    others/test_datas/sentences.jsonl   每行 {"id":"s0001","text":"...","language_id":"zh","industry":"美食"}
    others/test_datas/wav/s0001.wav       id 对应 wav 文件名(不含扩展名)
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.asr.audio_utils import get_wav_duration, resolve_industry
from apps.asr.models import Audio, Dataset, DatasetAudio


BASE_DIR = Path(settings.BASE_DIR).parent / "others" / "test_datas"
JSONL_PATH = BASE_DIR / "sentences.jsonl"
WAV_DIR = BASE_DIR / "wav"


def load_sentences() -> list[dict]:
    rows = []
    with JSONL_PATH.open(encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"sentences.jsonl 第 {line_no} 行 JSON 解析失败: {exc}") from exc
    return rows


class Command(BaseCommand):
    help = "从 sentences.jsonl + wav 目录导入真实音频"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dataset",
            default="真实测试集",
            help="导入后挂到的数据集名称，默认 真实测试集",
        )
        parser.add_argument(
            "--replace-fake",
            action="store_true",
            help="软删除 seed_demo 等假数据(demo_*.wav、占位路径 /media/audio/demo.wav)",
        )

    def handle(self, *args, **options):
        if not JSONL_PATH.exists():
            self.stderr.write(self.style.ERROR(f"找不到 {JSONL_PATH}"))
            return
        if not WAV_DIR.is_dir():
            self.stderr.write(self.style.ERROR(f"找不到 wav 目录: {WAV_DIR}"))
            return

        target_dir = Path(settings.MEDIA_ROOT) / "audio"
        target_dir.mkdir(parents=True, exist_ok=True)

        if options["replace_fake"]:
            removed = Audio.objects.filter(name__startswith="demo_").update(status=0)
            removed += Audio.objects.filter(audio_path="/media/audio/demo.wav").update(status=0)
            removed += Audio.objects.filter(name__in=["zh_guojun.wav", "en_10min_girl.wav"]).update(status=0)
            self.stdout.write(self.style.WARNING(f"已软删除旧/假数据 {removed} 条"))

        sentences = load_sentences()
        dataset, _ = Dataset.objects.get_or_create(
            name=options["dataset"],
            defaults={"language": "zh"},
        )
        self.stdout.write(self.style.SUCCESS(
            f"目标数据集: {dataset.name} (id={dataset.id})，待导入 {len(sentences)} 条"
        ))

        created, updated, skipped = 0, 0, 0
        imported_ids: list[int] = []

        with transaction.atomic():
            for item in sentences:
                sid = str(item.get("id", "")).strip()
                if not sid:
                    skipped += 1
                    continue

                src_wav = WAV_DIR / f"{sid}.wav"
                if not src_wav.exists():
                    self.stdout.write(self.style.WARNING(f"  [SKIP] 缺少音频: {src_wav.name}"))
                    skipped += 1
                    continue

                file_name = f"{sid}.wav"
                dst_wav = target_dir / file_name
                shutil.copy2(src_wav, dst_wav)

                duration = get_wav_duration(dst_wav)
                language = item.get("language_id") or "zh"
                industry = resolve_industry(item.get("industry"))
                ref_text = (item.get("text") or "").strip()
                url_path = f"{settings.MEDIA_URL}audio/{file_name}"

                obj, is_new = Audio.objects.update_or_create(
                    name=file_name,
                    defaults={
                        "language": language,
                        "audio_path": url_path,
                        "source": "outside",
                        "noise": "quiet",
                        "industry": industry,
                        "duration": duration,
                        "ref_text": ref_text,
                        "status": 1,
                    },
                )
                imported_ids.append(obj.id)
                DatasetAudio.objects.get_or_create(audio=obj, dataset=dataset)

                if is_new:
                    created += 1
                else:
                    updated += 1

                self.stdout.write(
                    f"  - {file_name:12s}  lang={language}  industry={industry:10s}  "
                    f"duration={duration:>6.2f}s  text_len={len(ref_text):>4d}  "
                    f"{'NEW' if is_new else 'UPDATED'}"
                )

        self.stdout.write(self.style.SUCCESS(
            f"[OK] 新增 {created} 条，更新 {updated} 条，跳过 {skipped} 条，"
            f"共 {len(imported_ids)} 条挂到《{dataset.name}》"
        ))
