#!/usr/bin/env bash
set -euo pipefail

# ── Log to both file and syslog ────────────────────────────────────────────────
exec > >(tee -a /tmp/deploy.log | logger -t deploy-script) 2>&1
set -x  # Print each command before executing

S3_BUCKET_NAME="$1"
IMAGE_TAG_FILE="/tmp/image_name.txt"

# ── Step 1: Download latest image tag from S3 ──────────────────────────────────
echo "📦 Downloading latest image tag from S3 bucket: $S3_BUCKET_NAME"
aws s3 cp "s3://${S3_BUCKET_NAME}/latest-image.txt" "$IMAGE_TAG_FILE"
IMAGE="$(< "$IMAGE_TAG_FILE")"
echo "✅ Image to deploy: $IMAGE"

# ── Step 2: Pull the latest Docker image ──────────────────────────────────────
echo "⬇️ Pulling image: $IMAGE"
docker pull "$IMAGE"

# ── Step 3: Stop & remove existing container safely ───────────────────────────
if docker ps -a --format '{{.Names}}' | grep -q "^address-validator$"; then
  echo "🛑 Stopping and removing existing container: address-validator"
  docker stop address-validator || true
  docker rm address-validator || true
else
  echo "ℹ️ No existing container named address-validator found."
fi

# ── Step 4: Run new container ─────────────────────────────────────────────────
echo "🚀 Starting new container with image: $IMAGE"
docker run -d \
  --name address-validator \
  -p 8000:8000 \
  --restart unless-stopped \
  "$IMAGE"

# ── Step 5: Verify deployment ─────────────────────────────────────────────────
echo "🔍 Verifying running container:"
docker ps --filter "name=address-validator" --format "table {{.Names}}\t{{.Image}}\t{{.Status}}"

echo "✅ Deployment complete"
