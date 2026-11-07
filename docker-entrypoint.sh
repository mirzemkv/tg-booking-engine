#!/bin/sh
set -e

MIGRATION_MODE="$(python -m src.scripts.migration_mode)"

if [ "$MIGRATION_MODE" = "stamp" ]; then
    echo "Existing database schema detected. Stamping Alembic head..."
    alembic stamp head
else
    echo "Applying database migrations..."
    alembic upgrade head
fi

exec "$@"
