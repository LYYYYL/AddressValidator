resource "aws_s3_bucket" "app" {
  bucket = "${var.environment}-${var.s3_bucket}"

  tags = {
    Name        = "${var.environment}-${var.s3_bucket}"
    Environment = var.environment
  }
}
