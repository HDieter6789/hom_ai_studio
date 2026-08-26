#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
"$script_dir/wait-for-postgres.sh" "${HOM_POSTGRES_HOST:-postgres}" "${HOM_POSTGRES_PORT:-5432}"

cd /srv/apps/api
alembic upgrade head

if [ "${HOM_SEED_ON_START:-false}" = "true" ]; then
  python -m app.seed
fi

exec "$@"
