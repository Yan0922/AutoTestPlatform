"""从远程服务器下载 ASR 模型压缩包并安装到本地."""
from __future__ import annotations

import re
import shutil
import tempfile
import zipfile
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen

from django.conf import settings
from django.db import transaction

from .models import AsrModel, AsrModelFile
from .model_utils import build_model_dir_path, persist_model_files_from_dir

ZIP_LINK_RE = re.compile(r"""href=["']([^"']+\.zip)["']""", re.I)
USER_AGENT = "AutoTestPlatform/1.0"

PHASE_LABELS = {
    "download": "下载压缩包",
    "extract": "解压",
    "install": "写入模型库",
}


class DownloadCancelled(Exception):
    """用户请求取消下载."""


def get_remote_base_url() -> str:
    return (getattr(settings, "ASR_MODEL_REMOTE_BASE_URL", "") or "").rstrip("/")


def normalize_version(version: str) -> str:
    v = (version or "").strip()
    if not v:
        return v
    return v if v.startswith("v") else f"v{v}"


def build_list_url(language: str, size: str) -> str:
    base = get_remote_base_url()
    return f"{base}/{language}/{size}/"


def build_zip_name(language: str, size: str, version: str) -> str:
    return f"{language}_{size}_{normalize_version(version)}.zip"


def build_zip_url(language: str, size: str, version: str) -> str:
    return urljoin(build_list_url(language, size), build_zip_name(language, size, version))


def _fetch_text(url: str, timeout: int = 30) -> str:
    req = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


def _download_file(
    url: str,
    dest: Path,
    timeout: int = 600,
    *,
    cancel_check=None,
    on_bytes=None,
) -> None:
    req = Request(url, headers={"User-Agent": USER_AGENT})
    chunk_size = 256 * 1024
    with urlopen(req, timeout=timeout) as resp, dest.open("wb") as out:
        total_raw = resp.headers.get("Content-Length")
        total = int(total_raw) if total_raw else None
        downloaded = 0
        while True:
            if cancel_check and cancel_check():
                raise DownloadCancelled()
            chunk = resp.read(chunk_size)
            if not chunk:
                break
            out.write(chunk)
            downloaded += len(chunk)
            if on_bytes:
                on_bytes(downloaded, total)


def fetch_directory_versions(language: str, size: str) -> list[dict]:
    """解析远程目录页，返回该语种+尺寸下可用的 zip 列表."""
    list_url = build_list_url(language, size)
    html = _fetch_text(list_url)
    prefix = f"{language}_{size}_"
    items: list[dict] = []
    seen: set[str] = set()

    for href in ZIP_LINK_RE.findall(html):
        zip_name = href.split("/")[-1]
        if not zip_name.lower().endswith(".zip"):
            continue
        stem = zip_name[:-4]
        if not stem.startswith(prefix):
            continue
        version = stem[len(prefix):]
        if not version or zip_name in seen:
            continue
        seen.add(zip_name)
        items.append({
            "language": language,
            "size": size,
            "version": version,
            "zip_name": zip_name,
            "url": urljoin(list_url, zip_name),
        })
    return items


def fetch_remote_catalog(languages: list[str], sizes: list[str]) -> dict:
    base_url = get_remote_base_url()
    if not base_url:
        raise ValueError("未配置远程模型地址 ASR_MODEL_REMOTE_BASE_URL")

    items: list[dict] = []
    errors: list[dict] = []
    seen_keys: set[tuple[str, str, str]] = set()

    for language in languages:
        for size in sizes:
            try:
                for item in fetch_directory_versions(language, size):
                    key = (item["language"], item["size"], item["version"])
                    if key in seen_keys:
                        continue
                    seen_keys.add(key)
                    items.append(item)
            except (HTTPError, URLError, TimeoutError, OSError) as exc:
                errors.append({
                    "language": language,
                    "size": size,
                    "error": str(exc),
                    "url": build_list_url(language, size),
                })

    items.sort(key=lambda x: (x["language"], x["size"], x["version"]))
    versions = sorted({item["version"] for item in items}, reverse=True)
    return {
        "base_url": base_url,
        "items": items,
        "versions": versions,
        "errors": errors,
    }


def resolve_extracted_model_dir(extract_dir: Path, zip_stem: str, version: str) -> Path:
    """定位解压后的模型文件目录（兼容双层目录结构）."""
    version_norm = normalize_version(version)
    candidates = [
        extract_dir / zip_stem / version_norm,
        extract_dir / zip_stem / version_norm.lstrip("v"),
        extract_dir / zip_stem,
        extract_dir,
    ]
    for candidate in candidates:
        if candidate.is_dir() and (
            list(candidate.glob("*.onnx"))
            or (candidate / "tokens.txt").is_file()
            or (candidate / "info.txt").is_file()
        ):
            return candidate

    for onnx in extract_dir.rglob("*.onnx"):
        return onnx.parent

    for candidate in candidates:
        if candidate.is_dir() and any(candidate.iterdir()):
            return candidate

    raise ValueError(f"解压后未找到模型文件目录: {zip_stem}")


def download_and_install_model(
    language: str,
    size: str,
    version: str,
    *,
    cancel_check=None,
    on_progress=None,
    item_index: int = 0,
) -> dict:
    """下载单个远程模型并写入 media 与数据库."""
    base_url = get_remote_base_url()
    if not base_url:
        raise ValueError("未配置远程模型地址 ASR_MODEL_REMOTE_BASE_URL")

    version_norm = normalize_version(version)
    zip_name = build_zip_name(language, size, version_norm)
    zip_stem = zip_name[:-4]
    model_name = zip_stem[:30]
    zip_url = build_zip_url(language, size, version_norm)

    existing = AsrModel.objects.filter(
        status=1,
        language=language,
        size=size,
        version=version_norm,
        name=model_name,
    ).first()
    if existing:
        if on_progress:
            on_progress({
                "item_index": item_index,
                "item_fraction": 1.0,
                "current_item": {"language": language, "size": size, "version": version_norm, "zip_name": zip_name},
                "phase": "skipped",
                "phase_label": "已存在",
                "message": "模型已存在，已跳过",
                "downloaded_bytes": 0,
                "total_bytes": None,
            })
        return {
            "status": "skipped",
            "language": language,
            "size": size,
            "version": version_norm,
            "model_id": existing.id,
            "name": existing.name,
            "message": "模型已存在，已跳过",
        }

    current_item = {"language": language, "size": size, "version": version_norm, "zip_name": zip_name}

    def emit(phase: str, item_fraction: float, message: str, downloaded: int = 0, total: int | None = None) -> None:
        if not on_progress:
            return
        on_progress({
            "item_index": item_index,
            "item_fraction": item_fraction,
            "current_item": current_item,
            "phase": phase,
            "phase_label": PHASE_LABELS.get(phase, phase),
            "message": message,
            "downloaded_bytes": downloaded,
            "total_bytes": total,
        })

    if cancel_check and cancel_check():
        raise DownloadCancelled()

    temp_kw = {"dir": settings.TEMP_ROOT} if getattr(settings, "TEMP_ROOT", None) else {}
    with tempfile.TemporaryDirectory(**temp_kw) as tmp:
        tmp_path = Path(tmp)
        zip_path = tmp_path / zip_name

        emit("download", 0.0, f"开始下载 {zip_name}")

        def on_bytes(done: int, total: int | None) -> None:
            if total and total > 0:
                frac = min(0.74, 0.75 * (done / total))
            else:
                frac = 0.35
            emit("download", frac, f"下载中 {zip_name}", done, total)

        _download_file(zip_url, zip_path, cancel_check=cancel_check, on_bytes=on_bytes)
        emit("download", 0.75, f"下载完成 {zip_name}")

        if cancel_check and cancel_check():
            raise DownloadCancelled()

        extract_dir = tmp_path / "extract"
        extract_dir.mkdir(parents=True, exist_ok=True)
        emit("extract", 0.78, "正在解压…")
        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(extract_dir)
        emit("extract", 0.9, "解压完成")

        if cancel_check and cancel_check():
            raise DownloadCancelled()

        files_dir = resolve_extracted_model_dir(extract_dir, zip_stem, version_norm)
        if not any(files_dir.iterdir()):
            raise ValueError(f"模型目录为空: {files_dir}")

        emit("install", 0.92, "正在写入模型库…")
        with transaction.atomic():
            instance = AsrModel.objects.create(
                name=model_name,
                language=language,
                version=version_norm,
                size=size,
            )
            instance.dir_path = build_model_dir_path(instance.name, instance.id)
            instance.save(update_fields=["dir_path"])
            file_count = persist_model_files_from_dir(instance, files_dir)

        emit("install", 1.0, "安装完成")

    return {
        "status": "ok",
        "language": language,
        "size": size,
        "version": version_norm,
        "model_id": instance.id,
        "name": instance.name,
        "file_count": file_count,
        "url": zip_url,
        "message": "下载并安装成功",
    }


def download_models_batch(
    languages: list[str],
    sizes: list[str],
    versions: list[str],
    *,
    cancel_check=None,
    on_progress=None,
) -> dict:
    results: list[dict] = []
    combos: list[tuple[str, str, str]] = []
    for language in languages:
        for size in sizes:
            for version in versions:
                combos.append((language, size, version))

    for item_index, (language, size, version) in enumerate(combos):
        if cancel_check and cancel_check():
            raise DownloadCancelled()
        try:
            results.append(
                download_and_install_model(
                    language,
                    size,
                    version,
                    cancel_check=cancel_check,
                    on_progress=on_progress,
                    item_index=item_index,
                )
            )
        except DownloadCancelled:
            raise
        except (HTTPError, URLError, TimeoutError, OSError, zipfile.BadZipFile, ValueError) as exc:
            results.append({
                "status": "failed",
                "language": language,
                "size": size,
                "version": normalize_version(version),
                "url": build_zip_url(language, size, version),
                "error": str(exc),
            })

    return {
        "ok": sum(1 for r in results if r.get("status") == "ok"),
        "skipped": sum(1 for r in results if r.get("status") == "skipped"),
        "failed": sum(1 for r in results if r.get("status") == "failed"),
        "results": results,
    }
