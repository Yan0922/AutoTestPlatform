#!/usr/bin/env bash
# 用户级 Redis 启停（端口 6380，无 root）
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
INSTALL_ROOT="${REDIS_INSTALL_ROOT:-/nasStore/yanliuping/software/redis}"
REDIS_SERVER="$INSTALL_ROOT/bin/redis-server"
REDIS_CLI="$INSTALL_ROOT/bin/redis-cli"
CONF="$INSTALL_ROOT/redis.conf"
PORT="${REDIS_PORT:-6380}"

cmd="${1:-status}"

if [[ ! -x "$REDIS_SERVER" ]]; then
  echo "[dev_redis] 未找到 redis-server，请先运行:"
  echo "  bash scripts/install_redis_user.sh"
  exit 1
fi

case "$cmd" in
  start)
    if "$REDIS_CLI" -p "$PORT" ping &>/dev/null; then
      echo "[dev_redis] Redis 已在运行 (127.0.0.1:$PORT)"
      exit 0
    fi
    "$REDIS_SERVER" "$CONF"
    sleep 0.5
    if "$REDIS_CLI" -p "$PORT" ping | grep -q PONG; then
      echo "[dev_redis] 已启动 127.0.0.1:$PORT"
    else
      echo "[dev_redis] 启动失败，查看日志: $INSTALL_ROOT/redis.log"
      exit 1
    fi
    ;;
  stop)
    if ! "$REDIS_CLI" -p "$PORT" ping &>/dev/null; then
      echo "[dev_redis] Redis 未运行"
      exit 0
    fi
    "$REDIS_CLI" -p "$PORT" shutdown nosave
    echo "[dev_redis] 已停止"
    ;;
  status|ping)
    if "$REDIS_CLI" -p "$PORT" ping &>/dev/null; then
      echo "[dev_redis] 运行中 127.0.0.1:$PORT -> PONG"
      "$REDIS_CLI" -p "$PORT" info server 2>/dev/null | grep -E 'redis_version|tcp_port|uptime_in_seconds' || true
    else
      echo "[dev_redis] 未运行 (127.0.0.1:$PORT)"
      exit 1
    fi
    ;;
  clear-download)
    # 清除 Celery 下载任务在 Redis 中的进度（解决进度条假卡住）
    keys=$("$REDIS_CLI" -p "$PORT" keys 'asr:download:*' 2>/dev/null || true)
    if [[ -z "$keys" ]]; then
      echo "[dev_redis] 无下载任务缓存"
    else
      echo "$keys" | xargs -r "$REDIS_CLI" -p "$PORT" del
      echo "[dev_redis] 已清除 asr:download:* 缓存"
    fi
    ;;
  *)
    echo "用法: $0 {start|stop|status|clear-download}"
    exit 1
    ;;
esac
