#!/usr/bin/env bash
# Sao lưu MySQL tự động lúc 02:00 mỗi ngày (NFR-AVL-02): mysqldump | gzip, giữ BACKUP_KEEP_DAYS ngày.
set -uo pipefail
KEEP="${BACKUP_KEEP_DAYS:-14}"
mkdir -p /backups
while true; do
  now=$(date +%s)
  next=$(date -d "tomorrow 02:00" +%s)
  today2=$(date -d "today 02:00" +%s)
  [ "$now" -lt "$today2" ] && next=$today2
  echo "[backup] Lần sao lưu tiếp theo: $(date -d @"$next")"
  sleep $((next - now))
  file="/backups/${DB_NAME}_$(date +%Y%m%d_%H%M%S).sql.gz"
  if mysqldump -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASSWORD" --single-transaction --routines --triggers \
       --set-gtid-purged=OFF "$DB_NAME" | gzip > "$file"; then
    echo "[backup] OK: $file ($(du -h "$file" | cut -f1))"
  else
    echo "[backup] LỖI khi sao lưu" >&2
    rm -f "$file"
  fi
  find /backups -name "*.sql.gz" -mtime +"$KEEP" -delete
done
