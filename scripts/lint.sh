#!/usr/bin/env bash
# Run all code quality checks. Pass --fix to auto-correct lint and format issues.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FIX=""
[[ "${1:-}" == "--fix" ]] && FIX="--fix"

echo "==> ruff lint"
uv run ruff check $FIX "$ROOT/backend"

echo "==> ruff format"
if [[ -n "$FIX" ]]; then
    uv run ruff format "$ROOT/backend"
else
    uv run ruff format --check "$ROOT/backend"
fi

echo "==> mypy"
uv run mypy "$ROOT/backend" --config-file "$ROOT/pyproject.toml"

echo ""
echo "All checks passed."
