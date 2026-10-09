variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "az" {
  type        = string
  description = "Availability zone for EBS volumes"
  default     = "us-east-1a"
}

variable "db_instance_type" {
  type    = string
  default = "t3.micro"
}

variable "control_node_ip" {
  description = "Private IP of the Control Node (Jenkins) for DB integration tests"
  type        = string
  default     = "172.31.132.151"
}

variable "db_ip" {
  type = map(string)
  default = {
    staging    = "172.31.133.10"
    production = "172.31.134.10"
  }
}

variable "private_subnet_cidr" {
  type = map(string)
  default = {
    staging    = "172.31.133.0/24"
    production = "172.31.134.0/24"
  }
}

variable "db_name" {
  type        = string
  description = "Application database name"
}

variable "db_user" {
  type        = string
  description = "MySQL user for Flask app authentication"
}

variable "db_password" {
  type      = string
  sensitive = true
}

variable "flask_image_tag" {
  type    = string
  default = "latest"
}
