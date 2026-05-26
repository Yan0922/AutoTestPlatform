@echo off
REM Windows 一键启动前端开发服务器
cd /d %~dp0..\frontend
if not exist node_modules (
  echo 安装前端依赖...
  npm install
)
npm run dev
