# 一键启动后端（PowerShell 版）
# 用法：在项目根目录或任意目录执行
#   powershell -ExecutionPolicy Bypass -File scripts\run_backend.ps1

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendDir = Join-Path $scriptDir "..\backend" | Resolve-Path
Set-Location $backendDir

if (-not (Test-Path .\venv\Scripts\python.exe)) {
    Write-Host "[1/4] venv 不存在，正在创建 ..." -ForegroundColor Yellow
    python -m venv venv
}

Write-Host "[2/4] 注入 .env 环境变量 ..." -ForegroundColor Cyan
if (Test-Path .\.env) {
    Get-Content .\.env | ForEach-Object {
        if ($_ -and $_ -notmatch '^\s*#') {
            $kv = $_ -split '=', 2
            if ($kv.Count -eq 2) {
                [Environment]::SetEnvironmentVariable($kv[0].Trim(), $kv[1].Trim(), 'Process')
            }
        }
    }
} else {
    Write-Host "[警告] .env 文件不存在，将使用默认配置" -ForegroundColor Yellow
}

Write-Host "[3/4] 执行数据库迁移 ..." -ForegroundColor Cyan
.\venv\Scripts\python.exe manage.py migrate

Write-Host "[4/4] 启动开发服务器 http://127.0.0.1:8000 ..." -ForegroundColor Green
.\venv\Scripts\python.exe manage.py runserver 0.0.0.0:8000
