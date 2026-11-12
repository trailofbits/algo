#!/bin/bash
set -euo pipefail

cd -- "$(git -C "$(dirname -- "$0")" rev-parse --show-toplevel)"
exec uv run --locked prek run --all-files "$@"
