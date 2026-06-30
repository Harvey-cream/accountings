#!/bin/sh
set -e

echo "[entrypoint] waiting for database..."
python - <<'PY'
import os
import sys
import time

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "accountsystem.settings")
django.setup()

from django.db import connection

for attempt in range(1, 31):
    try:
        connection.ensure_connection()
        print("[entrypoint] database is ready")
        break
    except Exception as exc:
        print(f"[entrypoint] database not ready ({attempt}/30): {exc}")
        time.sleep(2)
else:
    print("[entrypoint] database unavailable after 60s")
    sys.exit(1)
PY

echo "[entrypoint] running migrations..."
python manage.py migrate --noinput

echo "[entrypoint] seeding initial data (common/initia.py)..."
python common/initia.py

echo "[entrypoint] starting application..."
exec "$@"
