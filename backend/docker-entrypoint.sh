#!/bin/sh
# Đợi MySQL sẵn sàng; chỉ tự chạy migrate khi RUN_MIGRATIONS=1 (môi trường dev).
# Production: migrate được chạy riêng bởi bước Deploy trong GitHub Actions.
set -e
if [ "${DB_ENGINE:-mysql}" = "mysql" ]; then
  python - <<'PY'
import os, time, pymysql
for i in range(60):
    try:
        pymysql.connect(host=os.getenv("DB_HOST", "db"), port=int(os.getenv("DB_PORT", "3306")),
                        user=os.getenv("DB_USER"), password=os.getenv("DB_PASSWORD"), connect_timeout=2).close()
        break
    except Exception:
        print("Đang đợi MySQL...", flush=True)
        time.sleep(2)
PY
fi
if [ "${RUN_MIGRATIONS:-0}" = "1" ]; then
  python manage.py migrate --noinput
fi
exec "$@"
