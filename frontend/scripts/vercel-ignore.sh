#!/usr/bin/env bash
set -euo pipefail

if [ -z "${VERCEL_GIT_PREVIOUS_SHA:-}" ]; then
  # First deploy or no diff target → run the build
  exit 1
fi

if ! git cat-file -e "$VERCEL_GIT_PREVIOUS_SHA" 2>/dev/null; then
  git fetch origin "$VERCEL_GIT_PREVIOUS_SHA":"$VERCEL_GIT_PREVIOUS_SHA" --depth=1 || git fetch --unshallow
fi

if git diff --quiet "$VERCEL_GIT_PREVIOUS_SHA" "$VERCEL_GIT_COMMIT_SHA" -- frontend/; then
  # no frontend changes → skip build
  exit 0
fi

# frontend changed → run build
exit 1
