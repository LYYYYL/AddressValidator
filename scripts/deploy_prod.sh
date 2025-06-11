#!/bin/bash
set -e

# --- Configurable Defaults ---
PROJECT_NAME="address-validator"
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)

# --- Helper: Log message ---
log() {
  echo -e "\033[1;34m[INFO]\033[0m $1"
}

# --- Step 1: Build and push Docker image to ECR ---
build_and_push_image() {
  local ecr_registry="$1"
  local image_name="$2"
  local version="$3"

  log "Building Docker image..."
  docker build -f docker/Dockerfile.github -t $ecr_registry/$image_name:$version .

  log "Pushing Docker image to ECR..."
  docker push $ecr_registry/$image_name:$version

  echo "$ecr_registry/$image_name:$version" > image_name.txt
}

# --- Step 2: Upload image name to S3 ---
upload_image_tag_to_s3() {
  local bucket="$1"
  log "Uploading image_name.txt to s3://$bucket/latest-image.txt"
  aws s3 cp image_name.txt s3://$bucket/latest-image.txt
}

# --- Step 3: Upload this deploy script itself to S3 (optional but helpful) ---
upload_deploy_script_to_s3() {
  local bucket="$1"
  log "Uploading deploy script to s3://$bucket/deploy-address-validator-on-aws.sh"
  aws s3 cp "$SCRIPT_DIR/deploy_prod.sh" "s3://$bucket/deploy-address-validator-on-aws.sh"
}

# --- Step 4: Deploy to EC2 via SSM ---
deploy_via_ssm() {
  local instance_id="$1"
  local region="$2"
  local bucket="$3"

  log "Triggering remote deploy via SSM..."
  aws ssm send-command \
    --document-name "AWS-RunShellScript" \
    --instance-ids "$instance_id" \
    --region "$region" \
    --comment "Deploy latest image via uploaded script" \
    --parameters commands="[\
      'aws s3 cp s3://$bucket/deploy-address-validator-on-aws.sh /tmp/deploy.sh',\
      'chmod +x /tmp/deploy.sh',\
      '/tmp/deploy.sh $bucket'\
    ]" \
    --output text
}

# --- Main Execution ---
main() {
  if [[ $# -ne 6 ]]; then
    echo "Usage: $0 <ECR_REGISTRY> <IMAGE_NAME> <VERSION> <S3_BUCKET_NAME> <EC2_INSTANCE_ID> <AWS_REGION>"
    exit 1
  fi

  local ecr_registry="$1"
  local image_name="$2"
  local version="$3"
  local s3_bucket="$4"
  local ec2_instance="$5"
  local aws_region="$6"

  build_and_push_image "$ecr_registry" "$image_name" "$version"
  upload_image_tag_to_s3 "$s3_bucket"
  upload_deploy_script_to_s3 "$s3_bucket"
  deploy_via_ssm "$ec2_instance" "$aws_region" "$s3_bucket"
}

main "$@"
