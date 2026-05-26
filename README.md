# 算法测试平台（ASR / MT / TTS）

基于思维导图需求实现的算法测试平台，目前完整实现 **ASR** 模块（模型管理 / 数据集管理 / 数据池 / 测试任务 / 结果详情），MT 和 TTS 留接口占位。

技术栈：
- 后端：Python 3.10 + Django 4.2 + Django REST Framework + django-filter + openpyxl
- 数据库：SQLite（开发） / MySQL 8（生产）
- 前端：Vue 3 + Vite + Element Plus + Pinia + Vue Router + Axios
- 容器：Docker + docker-compose + Nginx 反向代理

---

## 一、目录结构

```
AutoTestPlatform/
├── backend/                 # Django 后端
│   ├── algotest/           # 项目目录
│   ├── apps/asr/           # ASR 业务应用
│   │   ├── models.py       # 数据模型(8张表)
│   │   ├── serializers.py
│   │   ├── views.py        # 全部 REST 接口
│   │   ├── urls.py
│   │   ├── filters.py      # 数据池多条件筛选
│   │   ├── tasks.py        # 测试任务执行 + 模拟ASR推理
│   │   ├── wer.py          # WER & S/I/D/Hit 算法
│   │   └── management/commands/seed_demo.py  # 演示数据
│   ├── manage.py
│   └── requirements.txt
├── frontend/                # Vue 3 前端
│   ├── src/
│   │   ├── api/            # axios 封装
│   │   ├── router/
│   │   ├── views/
│   │   │   ├── Layout.vue
│   │   │   └── asr/        # 5 个 ASR 页面
│   │   └── styles/
│   ├── index.html
│   ├── vite.config.js
│   └── package.json
├── docker/                 # Dockerfile + nginx 配置
├── docker-compose.yml      # 一键生产部署
└── scripts/                # Windows 一键启动脚本
```

---

## 二、数据库表设计

| 表 | 字段（关键） |
|---|---|
| `asr_model` | id, name, language, version, size, dir_path, status, created_at |
| `asr_model_file` | id, model_id, file_name, file_size, file_path |
| `dataset` | id, name, language, status, created_at |
| `audio` | id, name, language, audio_path, source, noise, industry, duration, ref_text, status, created_at |
| `dataset_audio` | id, dataset_id, audio_id（多对多） |
| `test_task` | id, name, model_id, task_status, created_at, finished_at |
| `test_task_dataset` | id, task_id, dataset_id, total_audio, total_duration, avg_wer, ret, s_cnt, i_cnt, d_cnt, hit_cnt |
| `test_audio_result` | id, task_id, dataset_id, audio_id, ref_text, hyp_text, wer, errors_json |

`status=1` 有效 / `status=0` 已删除（软删除）。

Django 会用 `python manage.py migrate` 自动建表，**不需要手写 SQL**。

---

## 三、开发模式启动（首次部署建议先用这种）

### 1. 启动后端（Windows 双击即可）

```bash
# 进入项目根目录
cd D:\Projects\AutoTestPlatform

# 方式 A：双击运行
scripts\dev_backend.bat

# 方式 B：手动执行
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py makemigrations asr
python manage.py migrate
python manage.py createsuperuser   # 可选，用于访问 /admin/
python manage.py seed_demo         # 可选，生成演示数据
python manage.py runserver 0.0.0.0:8000
```

后端启动后访问：
- API 根：http://127.0.0.1:8000/api/asr/
- Admin：http://127.0.0.1:8000/admin/

### 2. 启动前端

需要先安装 Node.js 18+。

```bash
# 方式 A：双击运行
scripts\dev_frontend.bat

# 方式 B：手动执行
cd frontend
npm install
npm run dev
```

前端启动后访问：http://127.0.0.1:5173

> 前端已在 `vite.config.js` 中配置 `/api` 和 `/media` 代理到 `127.0.0.1:8000`，无需 CORS 配置。

---

## 四、生产部署 - 推荐方式 A：Docker Compose 一键启动

服务器需安装 Docker + Docker Compose。

```bash
cd /path/to/AutoTestPlatform
docker compose up -d --build
```

启动后：
- 浏览器访问 `http://<服务器IP>/`（前端 + Nginx 代理后端）
- MySQL 端口 3306，Redis 端口 6379

执行迁移 / 创建超级用户 / 生成演示数据：

```bash
docker compose exec backend python manage.py createsuperuser
docker compose exec backend python manage.py seed_demo
```

修改 `docker-compose.yml` 中的密码与 SECRET_KEY 后再上生产环境。

---

## 五、生产部署 - 方式 B：Linux 上裸机 + Nginx + Gunicorn

适用于已有 Nginx 服务器的环境。

### 1. 后端

```bash
sudo apt install python3.10 python3.10-venv mysql-server redis-server
mysql -uroot -p
# CREATE DATABASE algotest CHARACTER SET utf8mb4;
# CREATE USER 'algotest'@'%' IDENTIFIED BY 'algotestpass';
# GRANT ALL ON algotest.* TO 'algotest'@'%';

cd /opt/AutoTestPlatform/backend
python3.10 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # 修改 DB_ENGINE=mysql 及账号

export $(grep -v '^#' .env | xargs)
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser

# 用 gunicorn 起 4 个 worker
gunicorn algotest.wsgi:application -b 127.0.0.1:8000 -w 4 --daemon
```

将 gunicorn 写入 systemd：

```ini
# /etc/systemd/system/algotest-backend.service
[Unit]
Description=AlgoTest Django Backend
After=network.target

[Service]
WorkingDirectory=/opt/AutoTestPlatform/backend
EnvironmentFile=/opt/AutoTestPlatform/backend/.env
ExecStart=/opt/AutoTestPlatform/backend/venv/bin/gunicorn algotest.wsgi:application -b 127.0.0.1:8000 -w 4
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now algotest-backend
```

### 2. 前端

```bash
cd /opt/AutoTestPlatform/frontend
npm install && npm run build
# dist/ 目录就是前端静态产物
```

### 3. Nginx 反代

```nginx
server {
    listen 80;
    server_name algotest.example.com;
    client_max_body_size 1024m;

    root /opt/AutoTestPlatform/frontend/dist;
    index index.html;

    location / { try_files $uri $uri/ /index.html; }
    location /api/    { proxy_pass http://127.0.0.1:8000; proxy_set_header Host $host; }
    location /media/  { proxy_pass http://127.0.0.1:8000; }
    location /static/ { proxy_pass http://127.0.0.1:8000; }
}
```

`sudo nginx -t && sudo systemctl reload nginx` 即可。

---

## 六、关键接口对照表

| 接口 | 方法 | 说明 |
|---|---|---|
| `/api/asr/models/` | GET / POST | 模型列表 / 上传新模型（multipart） |
| `/api/asr/models/{id}/` | GET / PUT / DELETE | 详情 / 修改 / 软删除 |
| `/api/asr/datasets/` | GET / POST | 数据集列表（含总音频数/总时长） |
| `/api/asr/datasets/{id}/remove-audios/` | POST | 从数据集中移除指定音频 |
| `/api/asr/audios/` | GET / POST | 音频池（支持多条件筛选 + 50条/页） |
| `/api/asr/audios/batch-delete/` | POST | 批量逻辑删除 |
| `/api/asr/audios/join-dataset/` | POST | 加入到一个或多个数据集 |
| `/api/asr/audios/{id}/update-text/` | PATCH | 修改 ref_text（数据池同步） |
| `/api/asr/audios/template/` | GET | 下载 Excel 模板 |
| `/api/asr/audios/parse-excel/` | POST | 上传 Excel 解析预览（不入库） |
| `/api/asr/audios/import/` | POST | 真正入库 |
| `/api/asr/tasks/` | GET / POST | 任务列表 / 创建（创建后会同步执行模拟推理） |
| `/api/asr/tasks/{id}/result/` | GET | 任务结果（含数据集统计 + 音频识别详情） |

---

## 七、关于 ASR 推理

代码里 `backend/apps/asr/tasks.py` 中的 `run_asr_infer()` 目前是**模拟实现**（基于 ref_text 加扰动）。
要接入真实模型时，把这个函数替换为：

```python
def run_asr_infer(audio: Audio, model) -> str:
    # 例如: 用 model.dir_path 指定的目录加载模型 ; 用 audio.audio_path 读音频
    # return your_asr_engine.transcribe(audio.audio_path)
    ...
```

后端使用的 WER / S / I / D / Hit 算法在 `apps/asr/wer.py`，是基于最小编辑距离的真实实现，前端会自动用红色标记错误字。

如果任务时间长，建议改为通过 Celery 异步执行：
1. 把 `tasks.py` 的 `execute_test_task` 加上 `@shared_task` 装饰器
2. 视图里改为 `execute_test_task.delay(task.id)`
3. 启动一个 worker：`celery -A algotest worker -l info`

---

## 八、思维导图需求覆盖度

| 模块 | 需求 | 状态 |
|---|---|---|
| 模型管理 | 列表/分页15/时间倒序/搜索/上传文件夹/修改/删除/详情 | ✅ |
| 数据集管理 | 增删改查/搜索/分两栏（右侧音频）/移除/翻页50 | ✅ |
| 数据池 | 多条件筛选/全选/批量删除/加入数据集/Excel导入与模板/文本修改 | ✅ |
| 测试任务 | 创建/列表/状态切换/运行结果/数据集统计/音频结果/红色标错/修改Ref同步数据池 | ✅ |
| MT / TTS | 菜单占位"敬请期待" | ✅ |

---

## 九、常见问题

1. **`mysqlclient` 安装失败**：Windows 上可改用 `pymysql`（在 `algotest/__init__.py` 加 `import pymysql; pymysql.install_as_MySQLdb()`）。开发阶段直接用默认 SQLite 即可。
2. **跨域报错**：开发模式下 Vite 已代理；生产模式由 Nginx 同源处理。如使用其他前端地址，请改 `settings.py` 的 `CORS_ALLOWED_ORIGINS`。
3. **上传文件夹**：依赖浏览器的 `webkitdirectory`，Chrome / Edge 都支持。
