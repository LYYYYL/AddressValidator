output "ecr_repo_url" {
  value = aws_ecr_repository.app.repository_url
}

output "s3_bucket_name" {
  value = aws_s3_bucket.app.bucket
}
