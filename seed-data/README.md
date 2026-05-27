# 种子数据说明

本目录仅保留**轻量元数据**；音频文件在 `backend/media/audio/{语种}/`，业务数据在 MySQL。

| 文件 | 说明 |
|------|------|
| `sentences.jsonl` | 每条音频的 id、参考文本、语种、行业（与数据库同步） |

## 重新导入 / 修复数据

```bash
cd backend
python manage.py import_media_audio --replace-fake --rebuild-demo-datasets
```

`import_media_audio` 会读取本目录的 `sentences.jsonl`，并到 `media/audio/{lang}/` 查找对应 wav。

## 从数据库刷新 jsonl 备份

```bash
cd backend
python manage.py export_seed_metadata
```

## 原 others/ 目录

原 `others/test_datas/` 中的 wav 与 jsonl 已迁入：

- wav → `backend/media/audio/zh/`、`en/` 等
- 文本与数据集关联 → 数据库 `audio` / `dataset_audio` 表

无需再保留 `others/` 下的重复 wav 副本。
