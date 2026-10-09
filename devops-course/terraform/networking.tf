# Private subnet with unique CIDR per workspace
resource "aws_subnet" "private" {
  vpc_id            = data.aws_vpc.main.id
  cidr_block        = var.private_subnet_cidr[terraform.workspace]
  availability_zone = var.az

  tags = {
    Name = "AWS-VPCB-PRIVATE-${terraform.workspace}"
  }
}

# Route private traffic through the Control Node/NAT instance
resource "aws_route_table" "private" {
  vpc_id = data.aws_vpc.main.id

  route {
    cidr_block           = "0.0.0.0/0"
    network_interface_id = data.aws_network_interface.nat.id
  }

  tags = {
    Name = "private-rt-${terraform.workspace}"
  }
}

resource "aws_route_table_association" "private" {
  subnet_id      = aws_subnet.private.id
  route_table_id = aws_route_table.private.id
}

# MySQL security group
resource "aws_security_group" "mysql" {
  name_prefix = "mysql-sg-${terraform.workspace}-"
  vpc_id      = data.aws_vpc.main.id

  ingress {
    from_port       = 3306
    to_port         = 3306
    protocol        = "tcp"
    security_groups = [aws_security_group.fargate.id]
  }

  ingress {
    from_port   = 3306
    to_port     = 3306
    protocol    = "tcp"
    cidr_blocks = ["${var.control_node_ip}/32"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "mysql-sg-${terraform.workspace}"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# ECS Fargate security group
resource "aws_security_group" "fargate" {
  name_prefix = "fargate-sg-${terraform.workspace}-"
  vpc_id      = data.aws_vpc.main.id

  ingress {
    from_port   = 5000
    to_port     = 5000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "fargate-sg-${terraform.workspace}"
  }

  lifecycle {
    create_before_destroy = true
  }
}
