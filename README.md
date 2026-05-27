# 算法测试平台（ASR / MT / TTS）

基于需求文档实现的算法测试平台。当前 **ASR 模块**已完整打通（模型管理 / 数据集管理 / 数据池 / 测试任务 / 结果详情），并接入 **K2 真实 ASR 推理引擎**；MT、TTS 为菜单占位，路由与公共组件已预留扩展位。

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Python 3.10+ · Django 4.2 · Django REST Framework · django-filter · openpyxl |
| 数据库 | MySQL 8（生产 / NAS 环境）· SQLite（可选本地开发） |
| 前端 | Vue 3 · Vite · Element Plus · Vue Router · Axios |
| 推理 | `model-test/k2_asr_model_test`（testAsr 二进制 + Python WER 脚本） |
| 部署 | Docker Compose · Nginx · Gunicorn（可选） |

---

## 一、目录结构

```
AutoTestPlatform/
├── backend/                          # Django 后端
│   ├── algotest/                     # 项目配置（settings / urls / wsgi）
│   ├── apps/asr/                     # ASR 业务应用
│   │   ├── models.py                 # 8 张业务表
│   │   ├── views.py                  # REST 接口
│   │   ├── tasks.py                  # 任务执行（后台线程 + K2 / 模拟）
│   │   ├── task_utils.py             # 任务名自动追加时间后缀
│   │   ├── wer.py                    # WER / S/I/D/Hit（比较前去除标点）
│   │   ├── remote_model.py           # 远程模型目录与下载
│   │   ├── remote_download_job.py    # 后台下载任务与进度
│   │   ├── k2_engine/                # K2 真实推理链路
│   │   │   ├── config.py             # 环境变量、staging 路径
│   │   │   ├── scp_src_builder.py    # 数据池 → .scp / .src
│   │   │   ├── single_infer.py       # 单模型推理（只跑任务选中的模型）
│   │   │   ├── task_runner.py        # 编排 staging → 推理 → 结果入库
│   │   │   └── result_importer.py    # K2 jsonl → test_audio_result
│   │   └── management/commands/
│   │       ├── import_media_audio.py # 导入 media/audio 真实 wav
│   │       ├── k2_build_staging.py   # 仅生成 scp/src（调试用）
│   │       └── seed_demo.py          # 演示假数据（不推荐生产）
│   ├── media/
│   │   ├── models/asr/               # 上传 / 下载的 ASR 模型目录
│   │   ├── audio/                    # 音频文件（zh/ en/ …）
│   │   └── k2_staging/               # K2 任务中间产物与推理结果
│   ├── .env.example
│   ├── requirements.txt
│   └── requirements-k2.txt           # K2 WER 脚本额外依赖
├── frontend/                         # Vue 3 前端
│   └── src/
│       ├── api/                      # axios 封装
│       ├── router/                   # 路由 + meta.js（面包屑 / 返回）
│       ├── components/
│       │   ├── PageHeader.vue        # 详情页头部（返回 + 标题 + meta）
│       │   └── AsrTextCompare.vue    # Ref / 预测上下对比 + 错误高亮
│       ├── composables/
│       │   ├── useStickyTable.js     # 表格区域自适应高度
│       │   └── useSplitPane.js       # 结果页左右分栏拖拽
│       └── views/asr/                # ModelList / DatasetList / DataPool / TaskList / TaskResult
├── seed-data/                        # 轻量元数据备份（sentences.jsonl）
│   └── sentences.jsonl               # 与 DB 同步；wav 在 backend/media/audio/
├── model-test/                       # K2 测试脚本（与平台同级，勿随意改接口）
│   └── k2_asr_model_test/
│       ├── testAsr                   # Linux 推理二进制
│       └── asr_test_code/            # scp/src 生成、WER 评估等
├── docker/                           # Dockerfile + nginx
├── docker-compose.yml
└── scripts/
    ├── dev_backend.sh                # Linux 后端一键启动
    ├── dev_backend.bat               # Windows 后端一键启动
    └── dev_frontend.bat              # Windows 前端一键启动
```

---

## 二、系统架构（ASR 测试任务）

```
用户创建任务（选 1 模型 + N 数据集）
        │
        ▼
POST /api/asr/tasks/  →  202 Accepted（后台线程执行，不阻塞 HTTP）
        │
        ▼
┌───────────────────────────────────────────────────────────┐
│  K2_ENGINE_ENABLED=1 且 testAsr 可用                       │
│  ─────────────────────────────────────────────────────    │
│  1. scp_src_builder：从数据池生成 .scp / .src（ref 去标点）  │
│     staging: media/k2_staging/{任务名_时间}/dataset_{id}_…  │
│  2. single_infer：对任务选中的单个模型目录跑 testAsr         │
│  3. result_importer：解析 jsonl，compute_wer 后写入 DB       │
└───────────────────────────────────────────────────────────┘
        │  K2 不可用（Windows 开发 / 未配置 testAsr）
        ▼
   tasks.py 模拟推理（基于 ref_text 加扰动，便于 UI 联调）
        │
        ▼
test_task / test_task_dataset / test_audio_result  →  前端结果页展示
```

**任务命名**：用户输入 `test` → 自动变为 `test_20260527_1438`（`task_utils.build_task_name`），staging 目录同名。

**参考文本编辑**：仅在 **数据池** 可修改 `ref_text`；数据集管理、结果详情均为只读展示。

---

## 三、数据库表设计

| 表 | 说明（关键字段） |
|----|------------------|
| `asr_model` | name, language, version, size, dir_path, status |
| `asr_model_file` | model_id, file_name, file_path |
| `dataset` | name, language, status |
| `audio` | name, language, audio_path, source, noise, industry, duration, **ref_text** |
| `dataset_audio` | dataset_id ↔ audio_id（多对多） |
| `test_task` | name, model_id, task_status(1进行中/2完成/3失败), error_message |
| `test_task_dataset` | 每数据集汇总：total_audio, avg_wer, ret, s/i/d/hit |
| `test_audio_result` | 每条音频：ref_text, hyp_text, wer, errors_json |

`status=1` 有效，`status=0` 软删除。表结构由 `python manage.py migrate` 自动创建。

---

## 四、环境变量（`backend/.env`）

复制 `backend/.env.example` 为 `.env` 后修改：

```bash
# 系统盘满时必须指向 NAS 等大容量路径
PLATFORM_TEMP_DIR=/nasStore/yanliuping/tmp

DB_ENGINE=mysql
DB_NAME=algotest
DB_USER=test
DB_PASSWORD=...
DB_HOST=127.0.0.1
DB_PORT=3307          # 按实际 MySQL 端口

# 远程模型下载（模型管理 → 下载模型）
ASR_MODEL_REMOTE_BASE_URL=http://192.168.x.x:8080/k2/asr

# K2 真实推理（Linux 服务器）
K2_ENGINE_ENABLED=1
# TESTASR_BIN=/path/to/model-test/k2_asr_model_test/testAsr
# K2_STAGING_DIR=          # 默认 backend/media/k2_staging
# K2_PROJECT_ROOT=         # 默认 <项目根>/model-test
```

K2 启用后需额外安装依赖：

```bash
cd backend
pip install -r requirements-k2.txt
```

---

## 五、开发环境启动

### Linux / NAS（推荐）

```bash
cd /nasStore/yanliuping/workspace/projects/AutoTestPlatform

# 后端（读取 .env、migrate、runserver）
bash scripts/dev_backend.sh
# 或手动：
cd backend && source venv/bin/activate   # 或 ae 等自定义 alias
pip install -r requirements.txt
pip install -r requirements-k2.txt       # K2 环境需要
cp .env.example .env                     # 首次
python manage.py migrate
python manage.py runserver 0.0.0.0:8000

# 前端
cd frontend
npm install
npm run dev
```

- 后端 API：http://127.0.0.1:8000/api/asr/
- 前端：http://127.0.0.1:5173（Vite 已代理 `/api`、`/media`）

### 导入真实音频（首次 / 替换假数据）

```bash
cd backend
python manage.py import_media_audio --replace-fake --rebuild-demo-datasets
```

扫描 `media/audio/{lang}/*.wav`，写入数据池并关联「日常对话集」「科技新闻集」等演示数据集。

### Windows

```bat
scripts\dev_backend.bat
scripts\dev_frontend.bat
```

Windows 上通常 `K2_ENGINE_ENABLED=0`，走模拟推理即可调试 UI。

---

## 六、常用管理命令

| 命令 | 说明 |
|------|------|
| `python manage.py export_seed_metadata` | 从 DB 导出 seed-data/sentences.jsonl |
| `python manage.py import_media_audio --replace-fake --rebuild-demo-datasets` | 从 seed-data + media/audio 导入 |
| `python manage.py k2_build_staging --task-id <id>` | 仅生成 scp/src，不跑推理（调试） |
| `python manage.py seed_demo` | 生成演示假数据（开发用） |
| `python manage.py createsuperuser` | Django Admin 账号 |

---

## 七、关键接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/asr/models/` | GET / POST | 模型列表 / 上传 |
| `/api/asr/models/remote-download/start/` | POST | 启动远程模型下载（后台） |
| `/api/asr/models/remote-download/status/` | GET | 下载进度 |
| `/api/asr/datasets/` | GET / POST | 数据集 CRUD |
| `/api/asr/datasets/{id}/remove-audios/` | POST | 从数据集移除音频 |
| `/api/asr/audios/` | GET | 数据池（多条件筛选 + 分页） |
| `/api/asr/audios/{id}/update-text/` | PATCH | **仅数据池**修改 ref_text |
| `/api/asr/audios/batch-delete/` | POST | 批量软删除 |
| `/api/asr/audios/join-dataset/` | POST | 加入数据集 |
| `/api/asr/audios/import/` | POST | Excel 批量导入 |
| `/api/asr/tasks/` | GET / POST | 任务列表 / 创建（**202 异步执行**） |
| `/api/asr/tasks/{id}/result/` | GET | 结果详情；参数 `dataset_id`, `page`, `page_size` |

---

## 八、前端交互说明

| 页面 | 要点 |
|------|------|
| 模型管理 | 本地上传 / 远程目录浏览 / 后台下载进度条 |
| 数据池 | 多条件筛选、Excel 导入、**唯一可编辑 ref_text 的入口** |
| 测试任务 | 创建后弹窗立即关闭；列表轮询「进行中」状态；同页跳转结果 |
| 结果详情 | 面包屑 `首页 / ASR·测试任务 / ASR·结果详情`；左右分栏可拖拽；Ref/预测上下对比；底部分页 |

公共路由 meta 见 `frontend/src/router/meta.js`，MT/TTS 接入时可复用 `taskResultMeta('mt')` 等。

---

## 九、WER 计算说明

- 实现位置：`backend/apps/asr/wer.py`
- 比较前对 ref / hyp **去除标点**（数据池展示仍保留原文）
- 生成 K2 `.src` 时同样去除标点，避免符号计入错误率
- 前端 `AsrTextCompare` 用 `errors_json.ops` 高亮替换 / 插入 / 漏识别

---

## 十、生产部署

### 方式 A：Docker Compose

```bash
docker compose up -d --build
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py createsuperuser
```

修改 `docker-compose.yml` 中的密码与 `SECRET_KEY` 后再上线。

### 方式 B：Linux 裸机 + Nginx + Gunicorn

参见原 `docker/nginx` 配置思路：前端 `npm run build` 产物由 Nginx 托管，`/api/`、`/media/` 反代 Gunicorn。

生产环境务必设置：

- `DJANGO_DEBUG=0`
- `PLATFORM_TEMP_DIR` 指向大容量磁盘
- `K2_ENGINE_ENABLED=1` 并配置 `TESTASR_BIN`

---

## 十一、功能覆盖度

| 模块 | 状态 |
|------|------|
| 模型管理（上传 / 远程下载 / 进度） | ✅ |
| 数据集管理（增删改查 / 音频列表只读） | ✅ |
| 数据池（筛选 / 导入 / 编辑文本） | ✅ |
| 测试任务（异步 K2 推理 / 模拟降级 / 轮询状态） | ✅ |
| 结果详情（分页 / 分栏 / 文本对比 / 面包屑返回） | ✅ |
| MT / TTS | 占位 |

---

## 十二、常见问题

1. **K2 任务失败：缺少 jiwer / MeCab**  
   `pip install -r requirements-k2.txt`

2. **下载模型 No space left on device**  
   在 `.env` 设置 `PLATFORM_TEMP_DIR` 到 NAS，并用 `scripts/dev_backend.sh` 启动。

3. **音频 404 / 任务无结果**  
   执行 `import_media_audio --replace-fake --rebuild-demo-datasets` 导入真实 wav。

4. **K2 已启用但仍走模拟**  
   检查 `testAsr` 是否可执行、`K2_PROJECT_ROOT` 是否指向含 `model-test` 的目录。

5. **mysqlclient 安装失败（Windows）**  
   开发阶段可 `DB_ENGINE=sqlite`；或使用 `pymysql` 替代。

6. **跨域**  
   开发靠 Vite 代理；生产靠 Nginx 同源。

---

## 仓库

GitHub: [Yan0922/AutoTestPlatform](https://github.com/Yan0922/AutoTestPlatform)
