@echo off
chcp 65001 >nul
REM ================================================================
REM Windows 一键启动后端开发服务器（基于 MySQL）
REM 使用前请确认 MySQL 已经启动，且已经创建数据库 algotest
REM ================================================================
cd /d %~dp0..\backend

if not exist venv (
  echo [1/4] 创建虚拟环境 venv ...
  python -m venv venv
)

call venv\Scripts\activate.bat

echo [2/4] 安装/校验依赖 ...
pip install -q -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

echo [3/4] 执行数据库迁移（首次会自动建表）...
python manage.py migrate

echo [4/4] 启动开发服务器 http://127.0.0.1:8000 ...
python manage.py runserver 0.0.0.0:8000
