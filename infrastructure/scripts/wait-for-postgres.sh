#!/usr/bin/env bash
# Blocks until Postgres accepts connections, or times out. Used by the API
# container's entrypoint so `docker compose up` doesn't race migrations
# against a Postgres container that hasn't finished starting yet.
set -euo pipefail

host="${1:-postgres}"
port="${2:-5432}"
timeout_seconds="${3:-60}"

elapsed=0
until pg_isready -h "$host" -p "$port" >/dev/null 2>&1; do
  if [ "$elapsed" -ge "$timeout_seconds" ]; then
    echo "Timed out waiting for Postgres at ${host}:${port}" >&2
    exit 1
  fi
  sleep 1
  elapsed=$((elapsed + 1))
done
