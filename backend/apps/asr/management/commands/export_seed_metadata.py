"""将数据库中的音频元数据导出到 seed-data/sentences.jsonl（备份 / 迁移用）."""
from __future__ import annotations

import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from apps.asr.models import INDUSTRY_CHOICES, Audio

DEFAULT_OUT = Path(settings.BASE_DIR).parent / "seed-data" / "sentences.jsonl"
INDUSTRY_LABEL = dict(INDUSTRY_CHOICES)


class Command(BaseCommand):
    help = "从数据库导出 sentences.jsonl 到 seed-data/（音频文件仍在 media/audio/）"

    def add_arguments(self, parser):
        parser.add_argument(
            "--output",
            default=str(DEFAULT_OUT),
            help="输出 jsonl 路径，默认 seed-data/sentences.jsonl",
        )

    def handle(self, *args, **options):
        out_path = Path(options["output"])
        out_path.parent.mkdir(parents=True, exist_ok=True)

        rows: list[dict] = []
        for audio in Audio.objects.filter(status=1).order_by("name"):
            stem = Path(audio.name).stem
            rows.append({
                "id": stem,
                "industry": INDUSTRY_LABEL.get(audio.industry, "未知"),
                "text": audio.ref_text or "",
                "language_id": audio.language,
            })

        with out_path.open("w", encoding="utf-8") as f:
            for row in rows:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")

        self.stdout.write(self.style.SUCCESS(
            f"已导出 {len(rows)} 条到 {out_path}\n"
            f"音频文件位置: {Path(settings.MEDIA_ROOT) / 'audio'}/{{语种}}/"
        ))
