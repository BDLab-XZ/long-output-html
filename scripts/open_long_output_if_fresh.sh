#!/usr/bin/env bash
set -euo pipefail

SIDECAR="${1:-/tmp/claude-last-html-path.txt}"
STAMP="${2:-/tmp/claude-long-output.stamp}"
MAX_AGE_SECONDS="${CLAUDE_LONG_OUTPUT_MAX_AGE_SECONDS:-1800}"

[[ -f "$SIDECAR" ]] || exit 0
[[ -f "$STAMP" ]] || exit 0

TARGET=$(tr -d '\r' < "$SIDECAR")
[[ -n "$TARGET" ]] || exit 0
[[ "$TARGET" == *.html ]] || exit 0
[[ -f "$TARGET" ]] || exit 0

now=$(date +%s)
mtime=$(stat -f %m "$TARGET" 2>/dev/null || echo 0)
stamp_mtime=$(stat -f %m "$STAMP" 2>/dev/null || echo 0)
age=$(( now - stamp_mtime ))

if (( age > MAX_AGE_SECONDS )); then
  rm -f "$STAMP"
  exit 0
fi

if (( stamp_mtime < mtime )); then
  rm -f "$STAMP"
  exit 0
fi

open "$TARGET" >/dev/null 2>&1 || true
rm -f "$STAMP"
