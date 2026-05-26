@echo off
cd /d %~dp0..\backend
call venv\Scripts\activate.bat
python manage.py seed_demo
