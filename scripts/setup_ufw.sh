#!/usr/bin/env bash
# Tường lửa VPS: chỉ chấp nhận 80/443 từ dải IP Cloudflare + SSH. Chạy: sudo ./scripts/setup_ufw.sh
# LƯU Ý: Docker publish port có thể bỏ qua UFW; xem docs/DEPLOY.md mục "UFW + Docker".
set -euo pipefail
SSH_PORT="${SSH_PORT:-22}"
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow "${SSH_PORT}/tcp" comment "SSH"
for ip in $(curl -fsS https://www.cloudflare.com/ips-v4) $(curl -fsS https://www.cloudflare.com/ips-v6); do
  ufw allow proto tcp from "$ip" to any port 80,443 comment "Cloudflare"
done
ufw --force enable
ufw status numbered
