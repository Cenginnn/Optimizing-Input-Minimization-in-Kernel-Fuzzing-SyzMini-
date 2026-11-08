#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${ROOT}/configs/v515.env"
if [[ -f "$ENV_FILE" ]]; then
  set -a
  source "$ENV_FILE"
  set +a
else
  echo "ERROR: Environment file not found: $ENV_FILE"
  exit 1
fi
: "${SYZKALLER_DIR:=${ROOT}/syzmini}"
: "${INFLUENCE_FILE:=${ROOT}/influencev5.15.txt}"

"${ROOT}/scripts/check_env.sh"
python3 "${ROOT}/scripts/generate_config.py"

MANAGER="${SYZKALLER_DIR}/bin/syz-manager"
CONFIG="${ROOT}/configs/generated/v515.cfg"
RUN_ID="${RUN_ID:-$(date +%Y%m%d-%H%M%S)}"
RUN_DURATION="${RUN_DURATION:-10m}"
RESULT_DIR="${ROOT}/experiments/results/${RUN_ID}"
mkdir -p "$RESULT_DIR"
cp "$CONFIG" "$RESULT_DIR/manager.cfg"
# 为每次实验创建独立的工作目录
mkdir -p "$RESULT_DIR/workdir"

# 修改本次实验的 manager.cfg
python3 - "$RESULT_DIR/manager.cfg" "$RESULT_DIR/workdir" <<'PY'
import json
import sys

config_path = sys.argv[1]
workdir = sys.argv[2]

with open(config_path, "r", encoding="utf-8") as f:
    config = json.load(f)

config["workdir"] = workdir

with open(config_path, "w", encoding="utf-8") as f:
    json.dump(config, f, indent=2)
    f.write("\n")
PY

printf 'run_id=%s\nstarted_at=%s\n' \
  "$RUN_ID" "$(date --iso-8601=seconds)" \
  >> "$RESULT_DIR/run-info.txt"

echo "Starting SyzMini..."
echo "Config: $RESULT_DIR/manager.cfg"
echo "Log: $RESULT_DIR/manager.log"

cd "$SYZKALLER_DIR"

set +e
timeout --signal=INT --kill-after=60s "$RUN_DURATION" "$MANAGER" \
    -config "$RESULT_DIR/manager.cfg" \
    -influence_read "$(realpath "$INFLUENCE_FILE")" \
    2>&1 | tee "$RESULT_DIR/manager.log"

status=${PIPESTATUS[0]}
set -e

printf 'exit_code=%s\nfinished_at=%s\n' \
  "$status" "$(date --iso-8601=seconds)" \
  >> "$RESULT_DIR/run-info.txt"

exit "$status"