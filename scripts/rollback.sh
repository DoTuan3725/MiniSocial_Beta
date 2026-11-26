#!/usr/bin/env bash
# Quay lui về phiên bản ổn định trước đó (< 30 giây): ./scripts/rollback.sh <sha-cũ>
# (Không cần revert code trên Git; image cũ vẫn nằm trên GHCR)
set -euo pipefail
TAG="${1:?Cần tag image (mã commit) muốn quay về}"
IMAGE_TAG="$TAG" "$(dirname "$0")/deploy_no_migrate.sh"
