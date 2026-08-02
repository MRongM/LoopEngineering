#!/bin/sh
set -eu

script_dir=$(CDPATH= cd -P "$(dirname "$0")" && pwd)

if [ -n "${CODEX_HOME:-}" ]; then
    codex_home="$CODEX_HOME"
else
    codex_home="${HOME:?HOME must be set when CODEX_HOME is unset}/.codex"
fi

exec python3 \
    "$script_dir/adapters/codex/scripts/manage.py" \
    update \
    --codex-home \
    "$codex_home"
