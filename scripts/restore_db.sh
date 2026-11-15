#!/usr/bin/env bash
# Khôi phục CSDL từ bản sao lưu: ./scripts/restore_db.sh backups/social_db_20261108_020000.sql.gz
set -euo pipefail
FILE="${1:?Cần đường dẫn tệp .sql.gz}"
source .env
gunzip -c "$FILE" | docker compose -f docker-compose.prod.yml exec -T db mysql -uroot -p"$DB_ROOT_PASSWORD" "$DB_NAME"
echo "Đã khôi phục từ $FILE"
