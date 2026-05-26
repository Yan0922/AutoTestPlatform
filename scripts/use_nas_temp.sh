#!/usr/bin/env bash
# 在当前 shell 中启用 NAS 临时目录（pip install、手动命令等）
# 用法: source /nasStore/yanliuping/workspace/projects/AutoTestPlatform/scripts/use_nas_temp.sh

_NAS_TEMP_ROOT="${PLATFORM_TEMP_DIR:-/nasStore/yanliuping/tmp}"
export PLATFORM_TEMP_DIR="$_NAS_TEMP_ROOT"
export TMPDIR="$_NAS_TEMP_ROOT"
export TEMP="$_NAS_TEMP_ROOT"
export TMP="$_NAS_TEMP_ROOT"
mkdir -p "$_NAS_TEMP_ROOT"
echo "已设置临时目录: $_NAS_TEMP_ROOT"
