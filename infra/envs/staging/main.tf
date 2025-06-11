provider "aws" {
  region = "ap-southeast-1"  # Singapore
}

module "app_infra" {
  source      = "../../modules/app_infra"
  environment = "staging"
}
