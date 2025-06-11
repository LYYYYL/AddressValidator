variable "aws_region" {
  type    = string
  default = "ap-southeast-2"
}

variable "ecr_name" {
  type    = string
  default = "address-validator"
}

variable "s3_bucket" {
  type    = string
  default = "address-validator-bucket"
}
