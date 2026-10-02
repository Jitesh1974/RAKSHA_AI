#!/usr/bin/env sh
set -eu
BASE_URL="${BASE_URL:-http://localhost:8000}"
curl -fsS "$BASE_URL/health/live"
echo
curl -fsS "$BASE_URL/health/llm"
echo
