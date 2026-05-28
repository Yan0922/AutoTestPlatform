#!/usr/bin/env bash
# 无 root：在用户目录编译安装 Redis（仅需 gcc/make）
set -euo pipefail

REDIS_VERSION="${REDIS_VERSION:-7.2.7}"
INSTALL_ROOT="${REDIS_INSTALL_ROOT:-/nasStore/yanliuping/software/redis}"
SRC_ROOT="${REDIS_SRC_ROOT:-/nasStore/yanliuping/software/src}"
DATA_DIR="${REDIS_DATA_DIR:-/nasStore/yanliuping/tmp/redis-data}"
PORT="${REDIS_PORT:-6380}"

TARBALL="redis-${REDIS_VERSION}.tar.gz"
URL="https://download.redis.io/releases/${TARBALL}"

mkdir -p "$SRC_ROOT" "$INSTALL_ROOT/bin" "$DATA_DIR"

if [[ -x "$INSTALL_ROOT/bin/redis-server" ]]; then
  echo "[install_redis] 已安装: $INSTALL_ROOT/bin/redis-server"
  "$INSTALL_ROOT/bin/redis-server" --version
  exit 0
fi

BUILD_DIR="$SRC_ROOT/redis-${REDIS_VERSION}"
if [[ ! -d "$BUILD_DIR" ]]; then
  echo "[install_redis] 下载 Redis ${REDIS_VERSION} ..."
  curl -fsSL "$URL" -o "$SRC_ROOT/$TARBALL"
  tar xf "$SRC_ROOT/$TARBALL" -C "$SRC_ROOT"
fi

echo "[install_redis] 编译中（约 1～2 分钟）..."
make -C "$BUILD_DIR" -j"$(nproc 2>/dev/null || echo 2)" BUILD_TLS=no

cp "$BUILD_DIR/src/redis-server" "$INSTALL_ROOT/bin/"
cp "$BUILD_DIR/src/redis-cli" "$INSTALL_ROOT/bin/"

CONF="$INSTALL_ROOT/redis.conf"
cat > "$CONF" <<EOF
# 用户级 Redis（无 root），供 Celery / 下载进度使用
port ${PORT}
bind 127.0.0.1
daemonize yes
pidfile ${INSTALL_ROOT}/redis.pid
dir ${DATA_DIR}
logfile ${INSTALL_ROOT}/redis.log
save ""
appendonly no
maxmemory 256mb
maxmemory-policy allkeys-lru
EOF

echo "[install_redis] 完成"
echo "  redis-server: $INSTALL_ROOT/bin/redis-server"
echo "  配置文件:     $CONF"
echo "  数据目录:     $DATA_DIR"
echo "  端口:         $PORT"
echo ""
echo "下一步: bash scripts/dev_redis.sh start"
