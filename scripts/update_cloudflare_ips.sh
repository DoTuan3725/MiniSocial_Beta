#!/usr/bin/env bash
# Cập nhật danh sách IP Cloudflare cho Nginx (real_ip) và UFW. Chạy trên VPS: sudo ./scripts/update_cloudflare_ips.sh
set -euo pipefail
OUT="$(dirname "$0")/../docker/nginx/cloudflare-realip.conf"
{
  echo "# Tự sinh lúc $(date -Iseconds) từ https://www.cloudflare.com/ips/"
  for ip in $(curl -fsS https://www.cloudflare.com/ips-v4) $(curl -fsS https://www.cloudflare.com/ips-v6); do
    echo "set_real_ip_from $ip;"
  done
  echo "real_ip_header CF-Connecting-IP;"
} > "$OUT"
echo "Đã cập nhật $OUT"
