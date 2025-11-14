output "alb_security_group_id" {
  description = "ALB security group ID"
  value       = aws_security_group.alb.id
}

output "ecs_api_security_group_id" {
  description = "ECS API security group ID"
  value       = aws_security_group.ecs_api.id
}

output "ecs_ui_security_group_id" {
  description = "ECS UI security group ID"
  value       = aws_security_group.ecs_ui.id
}

output "ecs_central_security_group_id" {
  description = "ECS Central security group ID"
  value       = aws_security_group.ecs_central.id
}

output "rds_security_group_id" {
  description = "RDS security group ID"
  value       = aws_security_group.rds.id
}
