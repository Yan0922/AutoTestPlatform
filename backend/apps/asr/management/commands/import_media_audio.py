"""从 sentences.jsonl 导入真实音频到 media/audio/{语种}/，并清理 seed_demo 假数据.

用法（推荐一键）:
    python manage.py import_media_audio --replace-fake --rebuild-demo-datasets

目录约定:
    others/test_datas/sentences.jsonl     元数据 id/text/language_id/industry
    others/test_datas/wav/{id}.wav        源 wav（若 media 下尚无则复制过去）
    backend/media/audio/{lang}/{id}.wav   平台实际使用的分语种路径

额外会扫描 media/audio/{lang}/*.wav，导入 jsonl 中未定义的 wav（ref_text 来自同名 .txt）。
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

DEFAULT_JSONL = Path(settings.BASE_DIR).parent / "others" / "test_datas" / "sentences.jsonl"
DEFAULT_SOURCE_WAV = Path(settings.BASE_DIR).parent / "others" / "test_datas" / "wav"
MEDIA_AUDIO = Path(settings.MEDIA_ROOT) / "audio"

# seed_demo 创建的数据集名
DEMO_DATASET_NAMES = ("日常对话集", "科技新闻集")

VALID_LANGS = {"zh", "en", "es", "ja", "ko", "ru", "fr", "de", "th", "it", "ar"}


def load_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open(encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path.name} 第 {line_no} 行 JSON 解析失败: {exc}") from exc
    return rows


def media_url_for(lang: str, filename: str) -> str:
    return f"{settings.MEDIA_URL}audio/{lang}/{filename}"


def ensure_wav_in_media(lang: str, file_name: str, source_wav_dir: Path) -> Path | None:
    """确保 wav 存在于 media/audio/{lang}/，必要时从源目录复制."""
    lang = lang if lang in VALID_LANGS else "zh"
    target_dir = MEDIA_AUDIO / lang
    target_dir.mkdir(parents=True, exist_ok=True)
    dst = target_dir / file_name
    if dst.is_file():
        return dst

    stem = Path(file_name).stem
    candidates = [
        source_wav_dir / file_name,
        MEDIA_AUDIO / file_name,  # 旧版扁平目录
    ]
    for src in candidates:
        if src.is_file():
            shutil.copy2(src, dst)
            return dst
    return None


def soft_delete_fake_audios() -> int:
    removed = 0
    removed += Audio.objects.filter(name__startswith="demo_", status=1).update(status=0)
    removed += Audio.objects.filter(audio_path="/media/audio/demo.wav", status=1).update(status=0)
    removed += Audio.objects.filter(audio_path__endswith="/demo.wav", status=1).update(status=0)
    return removed


def import_from_jsonl_row(
    item: dict,
    source_wav_dir: Path,
    dataset: Dataset | None,
) -> tuple[str, Audio | None]:
    sid = str(item.get("id", "")).strip()
    if not sid:
        return "skip", None

    language = (item.get("language_id") or "zh").strip()
    if language not in VALID_LANGS:
        language = "zh"

    file_name = f"{sid}.wav" if not sid.endswith(".wav") else sid
    wav_path = ensure_wav_in_media(language, file_name, source_wav_dir)
    if wav_path is None:
        return "missing", None

    duration = get_wav_duration(wav_path)
    ref_text = (item.get("text") or "").strip()
    industry = resolve_industry(item.get("industry"))

    obj, is_new = Audio.objects.update_or_create(
        name=file_name,
        defaults={
            "language": language,
            "audio_path": media_url_for(language, file_name),
            "source": "outside",
            "noise": "quiet",
            "industry": industry,
            "duration": duration,
            "ref_text": ref_text,
            "status": 1,
        },
    )
    if dataset is not None:
        DatasetAudio.objects.get_or_create(audio=obj, dataset=dataset)
    return ("new" if is_new else "updated"), obj


def scan_lang_dir(lang: str, known_names: set[str], dataset: Dataset | None) -> tuple[int, int]:
    """扫描 media/audio/{lang}/ 下未在 jsonl 中的 wav."""
    lang_dir = MEDIA_AUDIO / lang
    if not lang_dir.is_dir():
        return 0, 0
    created, updated = 0, 0
    for wav in sorted(lang_dir.glob("*.wav")):
        if wav.name in known_names:
            continue
        ref_text = ""
        txt = wav.with_suffix(".txt")
        if txt.is_file():
            ref_text = txt.read_text(encoding="utf-8", errors="ignore").strip()

        duration = get_wav_duration(wav)
        obj, is_new = Audio.objects.update_or_create(
            name=wav.name,
            defaults={
                "language": lang,
                "audio_path": media_url_for(lang, wav.name),
                "source": "outside",
                "noise": "quiet",
                "industry": "unknown",
                "duration": duration,
                "ref_text": ref_text,
                "status": 1,
            },
        )
        if dataset is not None:
            DatasetAudio.objects.get_or_create(audio=obj, dataset=dataset)
        if is_new:
            created += 1
        else:
            updated += 1
    return created, updated


class Command(BaseCommand):
    help = "导入真实音频到 media/audio/{语种}/ 并可选清理 seed_demo 假数据"

    def add_arguments(self, parser):
        parser.add_argument(
            "--jsonl",
            default=str(DEFAULT_JSONL),
            help="sentences.jsonl 路径",
        )
        parser.add_argument(
            "--source-wav-dir",
            default=str(DEFAULT_SOURCE_WAV),
            help="源 wav 目录（media 下没有时从此复制）",
        )
        parser.add_argument(
            "--dataset",
            default="真实测试集",
            help="jsonl 导入后挂到的数据集名称",
        )
        parser.add_argument(
            "--replace-fake",
            action="store_true",
            help="软删除 demo_*.wav 及占位路径 /media/audio/demo.wav",
        )
        parser.add_argument(
            "--rebuild-demo-datasets",
            action="store_true",
            help="用真实中文音频重建「日常对话集」「科技新闻集」（各约一半）",
        )
        parser.add_argument(
            "--scan-lang-dirs",
            action="store_true",
            default=True,
            help="扫描 media/audio/{lang}/ 下额外 wav（默认开启）",
        )
        parser.add_argument(
            "--no-scan-lang-dirs",
            action="store_false",
            dest="scan_lang_dirs",
            help="不扫描语种子目录中的额外 wav",
        )

    def handle(self, *args, **options):
        jsonl_path = Path(options["jsonl"])
        source_wav_dir = Path(options["source_wav_dir"])

        if options["replace_fake"]:
            removed = soft_delete_fake_audios()
            self.stdout.write(self.style.WARNING(f"已软删除假数据 {removed} 条"))

        if not jsonl_path.is_file():
            self.stderr.write(self.style.ERROR(f"找不到 {jsonl_path}"))
            return

        dataset, _ = Dataset.objects.get_or_create(
            name=options["dataset"],
            defaults={"language": "zh"},
        )
        self.stdout.write(self.style.SUCCESS(f"主数据集: {dataset.name} (id={dataset.id})"))

        sentences = load_jsonl(jsonl_path)
        created, updated, missing, skipped = 0, 0, 0, 0
        imported_zh_ids: list[int] = []
        known_names: set[str] = set()

        with transaction.atomic():
            for item in sentences:
                sid = str(item.get("id", "")).strip()
                file_name = f"{sid}.wav" if sid and not sid.endswith(".wav") else sid
                if file_name:
                    known_names.add(file_name)

                result, obj = import_from_jsonl_row(item, source_wav_dir, dataset)
                if result == "new":
                    created += 1
                    if obj and obj.language == "zh":
                        imported_zh_ids.append(obj.id)
                    if obj:
                        self.stdout.write(f"  + {obj.name}  ->  {obj.audio_path}")
                elif result == "updated":
                    updated += 1
                    if obj and obj.language == "zh":
                        imported_zh_ids.append(obj.id)
                elif result == "missing":
                    missing += 1
                    self.stdout.write(self.style.WARNING(f"  [MISS] {file_name}"))
                else:
                    skipped += 1

            if options["scan_lang_dirs"]:
                for lang_dir in sorted(MEDIA_AUDIO.iterdir()):
                    if not lang_dir.is_dir():
                        continue
                    lang = lang_dir.name
                    if lang not in VALID_LANGS:
                        self.stdout.write(self.style.WARNING(f"  [SKIP] 未识别语种目录: {lang}/"))
                        continue
                    lang_dataset = dataset
                    if lang == "en":
                        lang_dataset, _ = Dataset.objects.get_or_create(
                            name="英文测试集",
                            defaults={"language": "en"},
                        )
                    extra_c, extra_u = scan_lang_dir(lang, known_names, lang_dataset)
                    created += extra_c
                    updated += extra_u
                    if extra_c or extra_u:
                        self.stdout.write(
                            self.style.SUCCESS(f"  扫描 {lang}/: 新增 {extra_c}，更新 {extra_u}")
                        )

            if options["rebuild_demo_datasets"]:
                self._rebuild_demo_datasets(imported_zh_ids)

        self.stdout.write(self.style.SUCCESS(
            f"[完成] 新增 {created}，更新 {updated}，缺少文件 {missing}，跳过 {skipped}"
        ))

    def _rebuild_demo_datasets(self, zh_audio_ids: list[int]) -> None:
        if not zh_audio_ids:
            # 从数据库取全部有效中文音频
            zh_audio_ids = list(
                Audio.objects.filter(status=1, language="zh").order_by("name").values_list("id", flat=True)
            )
        if not zh_audio_ids:
            self.stdout.write(self.style.WARNING("没有可用的中文音频，跳过重建演示数据集"))
            return

        ds1, _ = Dataset.objects.get_or_create(name=DEMO_DATASET_NAMES[0], defaults={"language": "zh"})
        ds2, _ = Dataset.objects.get_or_create(name=DEMO_DATASET_NAMES[1], defaults={"language": "zh"})

        DatasetAudio.objects.filter(dataset__in=[ds1, ds2]).delete()

        mid = max(1, len(zh_audio_ids) // 2)
        for aid in zh_audio_ids[:mid]:
            DatasetAudio.objects.get_or_create(audio_id=aid, dataset=ds1)
        for aid in zh_audio_ids[mid:]:
            DatasetAudio.objects.get_or_create(audio_id=aid, dataset=ds2)

        self.stdout.write(self.style.SUCCESS(
            f"已重建数据集: 《{ds1.name}》{mid} 条，《{ds2.name}》{len(zh_audio_ids) - mid} 条"
        ))
