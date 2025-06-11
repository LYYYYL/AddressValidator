provider "aws" {
  region = var.aws_region
}

resource "aws_ecr_repository" "app" {
  name = var.ecr_name
}

resource "aws_s3_bucket" "app" {
  bucket = var.s3_bucket
  force_destroy = true
}
