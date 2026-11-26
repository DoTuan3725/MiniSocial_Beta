#!/usr/bin/env bash
# Như deploy.sh nhưng KHÔNG chạy migrate (dùng cho rollback: schema mới vẫn tương thích ngược).
set -euo pipefail
cd "$(dirname "$0")/.."
TAG="${IMAGE_TAG:?}"
sed -i "s/^IMAGE_TAG=.*/IMAGE_TAG=${TAG}/" .env
export IMAGE_TAG="$TAG"
docker compose -f docker-compose.prod.yml pull backend worker beat
docker compose -f docker-compose.prod.yml up -d --no-deps backend worker beat
echo "Đã chuyển sang phiên bản ${TAG}"
