#!/bin/bash
set -euo pipefail

IMAGE="$1"
echo "🐳 [DEBUG] Received IMAGE='$IMAGE'"

if [[ -z "$IMAGE" ]]; then
  echo "❌ ERROR: IMAGE variable is empty. Aborting."
  exit 1
fi

echo "🔍 Checking current container image and status..."
CURRENT_IMAGE=$(docker inspect --format='{{.Config.Image}}' address_validator 2>/dev/null || echo "")
IS_RUNNING=$(docker inspect --format='{{.State.Running}}' address_validator 2>/dev/null || echo "false")

if [[ "$CURRENT_IMAGE" == "$IMAGE" && "$IS_RUNNING" == "true" ]]; then
  echo "✅ Same image is already running. Skipping redeploy."
  exit 0
fi

echo "🛑 Stopping old container (if any)..."
docker stop address_validator || true
docker rm address_validator || true

echo "🔐 Logging into ECR..."
REGISTRY=$(echo "$IMAGE" | cut -d/ -f1)
REGION=$(echo "$REGISTRY" | cut -d. -f4)

if [[ "$REGISTRY" == *.amazonaws.com ]]; then
  aws ecr get-login-password --region "$REGION" | docker login --username AWS --password-stdin "$REGISTRY"
else
  echo "❌ ERROR: '$REGISTRY' does not look like a valid ECR registry."
  exit 1
fi

echo "📥 Pulling image: $IMAGE"
docker pull "$IMAGE"

echo "🚀 Running new container..."
docker run -d -p 8000:8000 --name address_validator "$IMAGE"

echo "✅ Deployment successful!"
