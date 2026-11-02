#!/bin/sh
# The standard test run: pinned environment (uv.lock), whole suite, every test must pass.
set -eu
cd "$(dirname "$0")/.."
uv sync --frozen --quiet
exec uv run --frozen pytest -q "$@"
