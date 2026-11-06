set -e

alembic -c persistence/alembic.ini upgrade head

exec uvicorn drivers.rest.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --reload \
    --reload-dir /app/config \
    --reload-dir /app/domain \
    --reload-dir /app/drivers \
    --reload-dir /app/exceptions \
    --reload-dir /app/persistence \
    --reload-dir /app/services \
    --reload-dir /app/utils
