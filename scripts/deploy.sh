#!/usr/bin/env bash
# Được GitHub Actions gọi qua SSH. Cập nhật backend không gián đoạn và chạy migration.
# Dùng tay: IMAGE_TAG=<sha> ./scripts/deploy.sh
set -euo pipefail
cd "$(dirname "$0")/.."
TAG="${IMAGE_TAG:-latest}"
sed -i "s/^IMAGE_TAG=.*/IMAGE_TAG=${TAG}/" .env
export IMAGE_TAG="$TAG"
docker compose -f docker-compose.prod.yml pull backend worker beat
docker compose -f docker-compose.prod.yml up -d --no-deps backend worker beat
docker compose -f docker-compose.prod.yml exec -T backend python manage.py migrate --noinput
docker compose -f docker-compose.prod.yml up -d nginx db redis db-backup
docker image prune -f
for i in $(seq 1 20); do
  if docker compose -f docker-compose.prod.yml exec -T backend curl -fsS http://localhost:8000/api/health/ >/dev/null; then
    echo "Triển khai thành công phiên bản ${TAG}"; exit 0
  fi
  sleep 3
done
echo "Health check thất bại sau khi triển khai ${TAG}" >&2
exit 1
