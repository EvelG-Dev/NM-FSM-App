# MySQL EC2 from Golden AMI
resource "aws_instance" "mysql_db" {
  ami                    = data.aws_ami.mysql_golden.id
  instance_type          = var.db_instance_type
  subnet_id              = aws_subnet.private.id
  private_ip             = var.db_ip[terraform.workspace]
  vpc_security_group_ids = [aws_security_group.mysql.id]
  iam_instance_profile   = "LabInstanceProfile"

  tags = {
    Name        = "${terraform.workspace}-db"
    Environment = terraform.workspace
    ManagedBy   = "terraform"
  }
}

resource "aws_ebs_volume" "mysql_data" {
  availability_zone = var.az
  size              = 20
  type              = "gp3"

  lifecycle {
    prevent_destroy = true
  }

  tags = {
    Name = "${terraform.workspace}-mysql-data"
  }
}

resource "aws_volume_attachment" "mysql_data" {
  device_name = "/dev/xvdf"
  volume_id   = aws_ebs_volume.mysql_data.id
  instance_id = aws_instance.mysql_db.id
}
