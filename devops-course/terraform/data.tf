# Professor-created resources. Terraform reads but does not manage these.

data "aws_vpc" "main" {
  tags = {
    Name = "AWS-VPCB-VPC"
  }
}

data "aws_subnet" "public" {
  tags = {
    Name = "AWS-VPCB-PUBLIC"
  }
}

data "aws_iam_role" "lab" {
  name = "LabRole"
}

data "aws_instance" "control_node" {
  filter {
    name   = "tag:Name"
    values = ["AWS-VPCB-NAT"]
  }
}

data "aws_network_interface" "nat" {
  filter {
    name   = "attachment.instance-id"
    values = [data.aws_instance.control_node.id]
  }
}

data "aws_ami" "mysql_golden" {
  most_recent = true
  owners      = ["self"]

  filter {
    name   = "name"
    values = ["mysql-golden-*"]
  }

  filter {
    name   = "tag:BuiltBy"
    values = ["packer"]
  }
}
