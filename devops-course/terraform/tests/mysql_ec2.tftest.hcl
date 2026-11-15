variables {
  aws_region       = "us-east-1"
  db_instance_type = "t3.micro"
}

run "mysql_ec2_uses_golden_ami" {
  command = plan
  assert {
    condition     = aws_instance.mysql_db.ami == data.aws_ami.mysql_golden.id
    error_message = "MySQL EC2 must launch from the Packer Golden AMI"
  }
  assert {
    condition     = data.aws_ami.mysql_golden.tags["BuiltBy"] == "packer"
    error_message = "The resolved AMI must be tagged BuiltBy=packer"
  }
}

run "ebs_volume_has_prevent_destroy" {
  command = plan
  assert {
    condition     = aws_ebs_volume.mysql_data.size >= 20
    error_message = "EBS data volume must be at least 20 GB"
  }
}

run "private_subnet_has_correct_cidr" {
  command = plan
  assert {
    condition     = aws_subnet.private.cidr_block == var.private_subnet_cidr["staging"]
    error_message = "Staging subnet must match its configured CIDR"
  }
}
