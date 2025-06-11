resource "aws_s3_bucket" "app" {
  bucket = "${var.environment}-address-validator-bucket"

  tags = {
    Name        = "${var.environment}-address-validator"
    Environment = var.environment
  }
}
