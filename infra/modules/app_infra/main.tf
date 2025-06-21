locals {
  name_prefix = "${var.environment}-${var.ec2_name}"
}

resource "aws_instance" "app" {
  ami           = data.aws_ami.ubuntu.id
  instance_type = "t2.micro"

  iam_instance_profile = aws_iam_instance_profile.ssm_profile.name
  tags = {
    Name = local.name_prefix
  }
}

# Create instance profile from the role
resource "aws_iam_instance_profile" "ssm_profile" {
  name = "${var.environment}-ssm-instance-profile"
  role = aws_iam_role.ssm_role.name
}
