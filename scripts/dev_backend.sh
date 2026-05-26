#!/usr/bin/env bash
# Linux：启动后端开发服务（自动使用 .env 中的 PLATFORM_TEMP_DIR）
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND="$ROOT/backend"
cd "$BACKEND"

_load_platform_temp() {
  local line key val
  if [[ -f .env ]]; then
    while IFS= read -r line || [[ -n "$line" ]]; do
      line="${line%%#*}"
      line="$(echo "$line" | xargs)"
      [[ -z "$line" || "$line" != *=* ]] && continue
      key="${line%%=*}"
      val="${line#*=}"
      val="${val%\"}"; val="${val#\"}"
      val="${val%\'}"; val="${val#\'}"
      if [[ "$key" == "PLATFORM_TEMP_DIR" && -n "$val" ]]; then
        export PLATFORM_TEMP_DIR="$val"
      fi
    done < .env
  fi
  export PLATFORM_TEMP_DIR="${PLATFORM_TEMP_DIR:-/nasStore/yanliuping/tmp}"
  export TMPDIR="$PLATFORM_TEMP_DIR"
  export TEMP="$PLATFORM_TEMP_DIR"
  export TMP="$PLATFORM_TEMP_DIR"
  mkdir -p "$PLATFORM_TEMP_DIR"
  echo "[dev_backend] 临时目录: $PLATFORM_TEMP_DIR"
}

_load_platform_temp

if [[ ! -d venv ]]; then
  echo "[dev_backend] 创建 venv ..."
  python3 -m venv venv
fi
# shellcheck source=/dev/null
source venv/bin/activate

pip install -q -r requirements.txt

python manage.py migrate
echo "[dev_backend] http://127.0.0.1:8000"
exec python manage.py runserver 0.0.0.0:8000
