#!/bin/bash
set -e

# Run from /backend

echo "Running migrations..."
# Use 'uv run' to execute alembic within the virtual environment
# Pointing to app/alembic.ini
uv run alembic -c app/alembic.ini upgrade head

echo "Migrations completed. Starting application..."

# Execute the CMD (also using uv run to ensure the app sees the packages)
exec uv run "$@"