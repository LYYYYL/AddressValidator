/*
terraform {
  backend "s3" {
    bucket       = "staging-address-validator-bucket"
    key          = "staging/terraform.tfstate"
    region       = "ap-southeast-1"
    encrypt      = true
    use_lockfile = true
  }
}
*/
