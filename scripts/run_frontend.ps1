# 一键启动前端（PowerShell 版）
# 用法：powershell -ExecutionPolicy Bypass -File scripts\run_frontend.ps1

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$frontendDir = Join-Path $scriptDir "..\frontend" | Resolve-Path
Set-Location $frontendDir

if (-not (Test-Path .\node_modules)) {
    Write-Host "[1/2] 安装前端依赖（首次较慢）..." -ForegroundColor Yellow
    npm install --registry=https://registry.npmmirror.com
}

Write-Host "[2/2] 启动前端 http://localhost:5173 ..." -ForegroundColor Green
npm run dev
