#!/usr/bin/env bash
set -euo pipefail

# ── log everything to a file + stdout ───────────────────────────────────────────
exec > >(tee -a /tmp/deploy.log | logger -t deploy-script) 2>&1
set -x      # bash prints every command as it runs

S3_BUCKET_NAME="$1"

aws s3 cp "s3://${S3_BUCKET_NAME}/latest-image.txt" /tmp/image_name.txt
IMAGE="$(< /tmp/image_name.txt)"

echo "✅ Will deploy image: $IMAGE"
echo "🕑 Current address-validator image (if running):"
docker inspect address-validator --format '{{.Config.Image}}' 2>/dev/null || echo "  (container not running)"

echo "🔄  docker pull $IMAGE"
docker pull "$IMAGE"

echo "🛑  Stopping existing container (if any)…"
docker stop address-validator || true
docker rm   address-validator || true

echo "🚀  Starting new container with: $IMAGE"
docker run -d -p 8000:8000 --restart unless-stopped --name address-validator "$IMAGE"

echo "📄  New container image:"
docker inspect address-validator --format '{{.Config.Image}}'
echo "✅ Deploy complete"
