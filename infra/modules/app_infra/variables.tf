variable "environment" {
  description = "The environment name (e.g., staging, prod)"
  type        = string
}

output "environment" {
  value = var.environment
}
variable "ecr_name" {
  type        = string
  default     = "address-validator"
  description = "ECR instance base name"
}

variable "ec2_name" {
  type        = string
  default     = "address-validator"
  description = "EC2 instance base name"
}

variable "s3_bucket" {
  type        = string
  default     = "address-validator-bucket"
  description = "S3 bucket instance base name"
}
