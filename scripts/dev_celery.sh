#!/usr/bin/env bash
# Linux：启动 Celery Worker（ASR 测试任务 + 远程模型下载）
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND="$ROOT/backend"
cd "$BACKEND"

if [[ -f .env ]]; then
  while IFS= read -r line || [[ -n "$line" ]]; do
    line="${line%%#*}"
    line="$(echo "$line" | xargs)"
    [[ -z "$line" || "$line" != *=* ]] && continue
    key="${line%%=*}"
    val="${line#*=}"
    val="${val%\"}"; val="${val#\"}"
    val="${val%\'}"; val="${val#\'}"
    export "$key=$val"
  done < .env
fi

if [[ ! -d venv ]]; then
  echo "[dev_celery] 请先运行 scripts/dev_backend.sh 创建 venv"
  exit 1
fi
# shellcheck source=/dev/null
source venv/bin/activate

CONCURRENCY="${CELERY_WORKER_CONCURRENCY:-1}"
echo "[dev_celery] broker=${CELERY_BROKER_URL:-redis://127.0.0.1:6379/0} concurrency=$CONCURRENCY"
echo "[dev_celery] 请确保 Redis 已启动；.env 中 CELERY_TASK_ALWAYS_EAGER=0 时本 worker 才会接管任务"

exec celery -A algotest worker -l info -c "$CONCURRENCY"
