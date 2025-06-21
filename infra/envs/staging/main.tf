module "app_infra" {
  source      = "../../modules/app_infra"
  environment = "staging"
  ecr_name    = "address-validator"
  ec2_name    = "address-validator"
  s3_bucket   = "address-validator-bucket"
}
