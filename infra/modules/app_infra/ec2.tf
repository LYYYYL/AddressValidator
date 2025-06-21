data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical (Ubuntu)

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# 1. Trust relationship: allow EC2 to assume role
data "aws_iam_policy_document" "ssm_assume_role" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }

    actions = ["sts:AssumeRole"]
  }
}

# 2. Create the role EC2 will assume
resource "aws_iam_role" "ssm_role" {
  name               = "${var.environment}-ssm-role"
  assume_role_policy = data.aws_iam_policy_document.ssm_assume_role.json
}

# 3. Inline policy for basic SSM actions
data "aws_iam_policy_document" "ssm_permissions" {
  statement {
    effect = "Allow"

    actions = [
      "ssm:SendCommand",
      "ssm:GetCommandInvocation",
      "ssm:DescribeInstanceInformation",
      "ssmmessages:*",
      "ec2messages:*",
      "ssm:UpdateInstanceInformation",
      "cloudwatch:PutMetricData",
      "ec2:DescribeInstances"
    ]

    resources = ["*"]
  }
}

# 4. Create the SSM policy
resource "aws_iam_policy" "ssm_policy" {
  name        = "${var.environment}-ssm-policy"
  description = "SSM policy for EC2"
  policy      = data.aws_iam_policy_document.ssm_permissions.json
}

# 5. Attach the policy to the role
resource "aws_iam_role_policy_attachment" "ssm_attach" {
  role       = aws_iam_role.ssm_role.name
  policy_arn = aws_iam_policy.ssm_policy.arn
}
