"""按 text 去重 sentences.jsonl，保留第一条，删除重复 wav 与数据库记录."""
import json
import os
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "algotest.settings")

import django

django.setup()

from django.conf import settings

from apps.asr.models import Audio

BASE = BACKEND_DIR.parent / "others" / "test_datas"
JSONL = BASE / "sentences.jsonl"
WAV_DIR = BASE / "wav"
MEDIA_DIR = Path(settings.MEDIA_ROOT) / "audio"


def main():
    rows = [
        json.loads(line)
        for line in JSONL.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    seen: set[str] = set()
    kept, removed_ids = [], []
    for item in rows:
        text = (item.get("text") or "").strip()
        if text in seen:
            removed_ids.append(item["id"])
        else:
            seen.add(text)
            kept.append(item)

    with JSONL.open("w", encoding="utf-8") as f:
        for item in kept:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    deleted_files = 0
    for sid in removed_ids:
        for p in (WAV_DIR / f"{sid}.wav", MEDIA_DIR / f"{sid}.wav"):
            if p.exists():
                p.unlink()
                deleted_files += 1

    removed_names = [f"{sid}.wav" for sid in removed_ids]
    db_removed = Audio.objects.filter(name__in=removed_names).update(status=0)

    print(f"jsonl: {len(rows)} -> {len(kept)} (removed {len(removed_ids)})")
    print(f"deleted wav files: {deleted_files}")
    print(f"db soft-deleted: {db_removed}")
    print("removed ids:", ", ".join(removed_ids))


if __name__ == "__main__":
    main()
