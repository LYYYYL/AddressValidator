#!/usr/bin/env bash
set -euo pipefail

exec > >(tee -a /tmp/deploy.log | logger -t deploy-script) 2>&1
set -x

S3_BUCKET_NAME="$1"
IMAGE_TAG_FILE="/tmp/image_name.txt"

# Step 1: Download latest image tag from S3
aws s3 cp "s3://${S3_BUCKET_NAME}/latest-image.txt" "$IMAGE_TAG_FILE"
IMAGE="$(< "$IMAGE_TAG_FILE")"

echo "✅ Image to deploy: $IMAGE"

aws ecr get-login-password --region ap-southeast-2 | docker login --username AWS --password-stdin 356892336264.dkr.ecr.ap-southeast-2.amazonaws.com

# Step 2: Pull image
docker pull "$IMAGE"

# Step 3: Stop & remove container if exists
if docker ps -a --format '{{.Names}}' | grep -q '^address-validator$'; then
  echo "🛑 Stopping existing container"
  docker stop address-validator || true
  docker rm address-validator || true
else
  echo "ℹ️ No existing container found"
fi

# Step 4: Run container
docker run -d -p 8000:8000 --restart unless-stopped --name address-validator "$IMAGE"

# Step 5: Show result
docker ps --filter "name=address-validator" --format "table {{.Names}}\t{{.Image}}\t{{.Status}}"

echo "✅ Deployment complete"
