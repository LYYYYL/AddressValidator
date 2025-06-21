output "ecr_repo_url" {
  value = aws_ecr_repository.app.repository_url
}

output "s3_bucket_name" {
  value = aws_s3_bucket.app.bucket
}

output "ssm_role_name" {
  value = aws_iam_role.ssm_role.name
}

output "ssm_instance_profile" {
  value = aws_iam_instance_profile.ssm_profile.name
}
