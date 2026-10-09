output "ecr_repository_url" {
  description = "Push Docker images here in Module 5"
  value       = local.ecr_repository_url
}

output "db_private_ip" {
  description = "MySQL IP for the current workspace"
  value       = aws_instance.mysql_db.private_ip
}
