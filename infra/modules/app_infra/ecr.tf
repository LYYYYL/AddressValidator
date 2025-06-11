resource "aws_ecr_repository" "app" {
  name = "${var.environment}-address-validator"
}
