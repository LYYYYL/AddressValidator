variable "environment" {
  description = "The environment name (e.g., staging, prod)"
  type        = string
}

output "environment" {
  value = var.environment
}
