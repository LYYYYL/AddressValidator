#!/bin/bash
set -e

S3_BUCKET_NAME="$1"

aws s3 cp s3://$S3_BUCKET_NAME/latest-image.txt /tmp/image_name.txt
IMAGE=$(cat /tmp/image_name.txt)

echo "✅ Pulling image: $IMAGE"
docker pull "$IMAGE"
docker stop address-validator || true
docker rm address-validator || true
docker run -d -p 8000:8000 --restart unless-stopped --name address-validator "$IMAGE"
