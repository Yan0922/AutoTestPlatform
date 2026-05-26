"""
生成 ASR 算法测试平台的 XMind 文件
XMind 8/2020 格式：zip 包含 content.json
"""
import json
import zipfile
import os

# ── XMind content.json 数据结构 ──────────────────────────────────────────────

def node(title, children=None, note=None):
    n = {"title": title, "children": {"attached": children or []}}
    if note:
        n["notes"] = {"plain": {"content": note}}
    return n

root = node("ASR 算法测试平台", [

    # ══════════════════════════════════════════════════════
    # 1. 系统架构
    # ══════════════════════════════════════════════════════
    node("系统架构", [
        node("前端 (Vue 3 + Vite)", [
            node("UI 框架：Element Plus"),
            node("状态管理：Pinia"),
            node("路由：Vue Router 4"),
            node("HTTP：Axios"),
            node("图表：ECharts 5"),
            node("音频播放：wavesurfer.js"),
        ]),
        node("后端 (Django 4.x + DRF)", [
            node("REST API：Django REST Framework"),
            node("任务队列：Celery + Redis"),
            node("文件存储：本地 media/ 目录"),
            node("数据库：SQLite（开发） / PostgreSQL（生产）"),
            node("跨域：django-cors-headers"),
            node("认证：JWT (djangorestframework-simplejwt)"),
        ]),
        node("部署方案 (Windows 单机)", [
            node("后端：python manage.py runserver 或 waitress"),
            node("前端：npm run build → Django 托管静态文件"),
            node("任务队列：celery -A core worker --pool=solo"),
            node("Redis：Windows 版 Redis 或 WSL"),
            node("一键启动脚本：start.bat"),
        ]),
    ]),

    # ══════════════════════════════════════════════════════
    # 2. 功能模块
    # ══════════════════════════════════════════════════════
    node("功能模块", [

        # 2.1 用户与权限
        node("用户与权限管理", [
            node("用户注册 / 登录 / 登出"),
            node("JWT Token 认证"),
            node("角色：管理员 / 普通用户"),
            node("个人信息修改 / 密码重置"),
        ]),

        # 2.2 模型管理
        node("模型管理", [
            node("模型信息", [
                node("模型名称、版本、描述"),
                node("模型类型：ASR"),
                node("API 地址（HTTP 接口）"),
                node("请求格式配置（headers、参数映射）"),
                node("响应字段映射（识别文本字段路径）"),
                node("状态：启用 / 禁用"),
                node("创建人、创建时间"),
            ]),
            node("模型连通性测试（ping）"),
            node("模型列表 / 新增 / 编辑 / 删除"),
        ]),

        # 2.3 数据集管理
        node("数据集管理", [
            node("数据集信息", [
                node("数据集名称、描述、语言"),
                node("领域标签（通用、医疗、金融…）"),
                node("创建人、创建时间"),
                node("音频总数、总时长统计"),
            ]),
            node("数据导入", [
                node("批量上传：zip 包（wav + txt 对）"),
                node("单条上传：单个 wav + 对应文本"),
                node("导入进度条显示"),
                node("格式校验：采样率、时长、编码"),
            ]),
            node("数据条目管理", [
                node("条目列表（音频ID、文件名、时长、参考文本）"),
                node("在线播放音频"),
                node("单条编辑参考文本"),
                node("批量删除"),
            ]),
            node("数据集导出（zip）"),
        ]),

        # 2.4 测试任务
        node("测试任务管理", [
            node("任务创建", [
                node("选择模型（单选）"),
                node("选择数据集（单选）"),
                node("任务名称、描述、优先级"),
                node("并发数配置"),
                node("超时时间配置"),
            ]),
            node("任务状态流转", [
                node("待执行 → 执行中 → 已完成 / 失败"),
                node("支持暂停 / 取消"),
                node("实时进度（已测/总数）"),
            ]),
            node("任务执行（Celery 异步）", [
                node("逐条调用模型 API"),
                node("记录识别结果与耗时"),
                node("计算 RTF（实时率）"),
                node("失败重试机制"),
            ]),
            node("任务列表 / 详情 / 删除"),
        ]),

        # 2.5 测试结果与评测
        node("测试结果与评测", [
            node("评测指标计算", [
                node("WER（词错误率）"),
                node("CER（字符错误率）"),
                node("RTF（实时率）"),
                node("平均推理耗时"),
                node("成功率 / 失败率"),
            ]),
            node("结果明细", [
                node("条目级：参考文本 vs 识别文本"),
                node("差异高亮（插入/删除/替换标注）"),
                node("音频在线播放"),
                node("单条耗时、RTF"),
            ]),
            node("结果汇总", [
                node("任务级汇总统计"),
                node("按数据集/模型对比"),
            ]),
            node("结果导出", [
                node("导出 Excel（明细 + 汇总）"),
                node("导出 JSON"),
            ]),
        ]),

        # 2.6 对比分析
        node("对比分析", [
            node("多模型横向对比", [
                node("选择同一数据集的多个任务"),
                node("WER / CER / RTF 对比表格"),
                node("雷达图 / 柱状图可视化"),
            ]),
            node("历史趋势", [
                node("同一模型跨时间 WER/CER 折线图"),
                node("版本迭代效果追踪"),
            ]),
        ]),

        # 2.7 数据统计看板
        node("数据统计看板（Dashboard）", [
            node("任务总数 / 今日新增"),
            node("模型数量 / 数据集数量"),
            node("平均 WER / CER 趋势"),
            node("最近任务列表"),
            node("各模型性能排行"),
        ]),

    ]),

    # ══════════════════════════════════════════════════════
    # 3. 数据库设计
    # ══════════════════════════════════════════════════════
    node("数据库设计", [
        node("users（用户表）", [
            node("id, username, email, password_hash"),
            node("role: admin/user"),
            node("created_at, updated_at, is_active"),
        ]),
        node("asr_models（模型表）", [
            node("id, name, version, description"),
            node("api_url, request_method, headers_json"),
            node("audio_field, text_response_path"),
            node("status: active/inactive"),
            node("created_by(FK), created_at"),
        ]),
        node("datasets（数据集表）", [
            node("id, name, description, language, domain"),
            node("total_count, total_duration_sec"),
            node("created_by(FK), created_at"),
        ]),
        node("audio_items（音频条目表）", [
            node("id, dataset(FK)"),
            node("file_path, filename, duration_sec, sample_rate"),
            node("reference_text"),
            node("created_at"),
        ]),
        node("test_tasks（测试任务表）", [
            node("id, name, description, priority"),
            node("model(FK), dataset(FK)"),
            node("status: pending/running/done/failed/cancelled"),
            node("concurrency, timeout_sec"),
            node("total_count, finished_count, failed_count"),
            node("started_at, finished_at"),
            node("created_by(FK), created_at"),
        ]),
        node("test_results（测试结果明细表）", [
            node("id, task(FK), audio_item(FK)"),
            node("hypothesis_text（识别结果）"),
            node("wer, cer, rtf, latency_ms"),
            node("status: success/failed"),
            node("error_message"),
            node("created_at"),
        ]),
        node("task_metrics（任务汇总指标表）", [
            node("id, task(FK, OneToOne)"),
            node("avg_wer, avg_cer, avg_rtf, avg_latency_ms"),
            node("success_rate, total_duration_sec"),
            node("calculated_at"),
        ]),
    ]),

    # ══════════════════════════════════════════════════════
    # 4. API 接口规划
    # ══════════════════════════════════════════════════════
    node("API 接口规划 (RESTful)", [
        node("/api/auth/", [
            node("POST /login/"),
            node("POST /logout/"),
            node("POST /register/"),
            node("GET/PUT /profile/"),
        ]),
        node("/api/models/", [
            node("GET / POST（列表/新增）"),
            node("GET / PUT / DELETE /{id}/"),
            node("POST /{id}/ping/（连通性测试）"),
        ]),
        node("/api/datasets/", [
            node("GET / POST（列表/新增）"),
            node("GET / PUT / DELETE /{id}/"),
            node("POST /{id}/import/（批量导入）"),
            node("GET /{id}/items/（条目列表）"),
            node("GET /{id}/export/（导出zip）"),
        ]),
        node("/api/tasks/", [
            node("GET / POST（列表/创建）"),
            node("GET / DELETE /{id}/"),
            node("POST /{id}/start/"),
            node("POST /{id}/cancel/"),
            node("GET /{id}/progress/（实时进度）"),
            node("GET /{id}/results/（明细列表）"),
            node("GET /{id}/metrics/（汇总指标）"),
            node("GET /{id}/export/（导出Excel/JSON）"),
        ]),
        node("/api/dashboard/", [
            node("GET /stats/（总览统计）"),
            node("GET /trend/（WER/CER趋势）"),
        ]),
        node("/api/compare/", [
            node("POST /models/（多模型对比）"),
        ]),
    ]),

    # ══════════════════════════════════════════════════════
    # 5. 项目目录结构
    # ══════════════════════════════════════════════════════
    node("项目目录结构", [
        node("backend/ (Django)", [
            node("core/ （Django 项目配置）"),
            node("apps/users/"),
            node("apps/models_mgr/"),
            node("apps/datasets/"),
            node("apps/tasks/"),
            node("apps/results/"),
            node("apps/dashboard/"),
            node("media/ （上传文件）"),
            node("requirements.txt"),
            node("manage.py"),
        ]),
        node("frontend/ (Vue 3)", [
            node("src/views/ （页面）"),
            node("src/components/ （组件）"),
            node("src/stores/ （Pinia）"),
            node("src/api/ （Axios封装）"),
            node("src/router/"),
            node("src/utils/（WER/CER计算工具）"),
        ]),
        node("deploy/ （部署脚本）", [
            node("start.bat （一键启动）"),
            node("stop.bat"),
            node("install.bat （依赖安装）"),
            node("README.md"),
        ]),
    ]),

    # ══════════════════════════════════════════════════════
    # 6. 部署方案（Windows 单机）
    # ══════════════════════════════════════════════════════
    node("部署方案（Windows 单机）", [
        node("环境依赖", [
            node("Python 3.10+"),
            node("Node.js 18+"),
            node("Redis for Windows"),
            node("Git（可选）"),
        ]),
        node("安装步骤", [
            node("1. pip install -r requirements.txt"),
            node("2. python manage.py migrate（初始化数据库）"),
            node("3. python manage.py createsuperuser"),
            node("4. npm install && npm run build"),
            node("5. python manage.py collectstatic"),
        ]),
        node("启动方式", [
            node("start.bat 一键启动所有服务"),
            node("Django: waitress-serve --port=8000"),
            node("Celery: celery -A core worker --pool=solo -l info"),
            node("Redis: redis-server.exe"),
            node("访问: http://localhost:8000"),
        ]),
        node("后续可扩展", [
            node("Docker Compose 容器化"),
            node("Nginx 反向代理"),
            node("PostgreSQL 替换 SQLite"),
        ]),
    ]),

    # ══════════════════════════════════════════════════════
    # 7. 暂缓模块（MT / TTS）
    # ══════════════════════════════════════════════════════
    node("暂缓模块（预留扩展）", [
        node("MT 机器翻译测试", [
            node("BLEU 评分"),
            node("翻译对比"),
        ]),
        node("TTS 语音合成测试", [
            node("MOS 评分"),
            node("音频质量评估"),
        ]),
    ]),
])

content = [
    {
        "id": "root-sheet",
        "class": "sheet",
        "title": "ASR 算法测试平台",
        "rootTopic": root,
        "extensions": [],
    }
]

# ── 写入 XMind 文件 ──────────────────────────────────────────────────────────
output_dir = r"d:\Projects\AutoTestPlatform"
xmind_path = os.path.join(output_dir, "ASR算法测试平台规划.xmind")

with zipfile.ZipFile(xmind_path, "w", zipfile.ZIP_DEFLATED) as zf:
    zf.writestr("content.json", json.dumps(content, ensure_ascii=False, indent=2))
    # metadata
    zf.writestr("metadata.json", json.dumps({
        "creator": {"name": "Kiro", "version": "1.0"},
        "version": "2.0"
    }, ensure_ascii=False))

print(f"XMind 文件已生成：{xmind_path}")
