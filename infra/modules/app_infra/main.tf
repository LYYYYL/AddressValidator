locals {
  name_prefix = "${var.environment}-address-validator"
}

resource "aws_instance" "app" {
  ami = data.aws_ami.ubuntu.id
  instance_type = "t2.micro"
  tags = {
    Name = local.name_prefix
  }
}
