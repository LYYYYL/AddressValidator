resource "aws_ecr_repository" "app" {
  name = "${var.environment}-${var.ecr_name}"
}
