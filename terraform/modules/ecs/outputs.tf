output "cluster_id" {
  description = "ECS cluster ID"
  value       = aws_ecs_cluster.main.id
}

output "cluster_name" {
  description = "ECS cluster name"
  value       = aws_ecs_cluster.main.name
}

output "cluster_arn" {
  description = "ECS cluster ARN"
  value       = aws_ecs_cluster.main.arn
}

# API Service
output "api_service_id" {
  description = "API service ID"
  value       = aws_ecs_service.api.id
}

output "api_service_name" {
  description = "API service name"
  value       = aws_ecs_service.api.name
}

output "api_task_definition_arn" {
  description = "API task definition ARN"
  value       = aws_ecs_task_definition.api.arn
}

# UI Service
output "ui_service_id" {
  description = "UI service ID"
  value       = aws_ecs_service.ui.id
}

output "ui_service_name" {
  description = "UI service name"
  value       = aws_ecs_service.ui.name
}

output "ui_task_definition_arn" {
  description = "UI task definition ARN"
  value       = aws_ecs_task_definition.ui.arn
}

# Central Service
output "central_service_id" {
  description = "Central service ID"
  value       = aws_ecs_service.central.id
}

output "central_service_name" {
  description = "Central service name"
  value       = aws_ecs_service.central.name
}

output "central_task_definition_arn" {
  description = "Central task definition ARN"
  value       = aws_ecs_task_definition.central.arn
}

# CloudWatch Log Groups
output "api_log_group_name" {
  description = "API CloudWatch log group name"
  value       = aws_cloudwatch_log_group.api.name
}

output "ui_log_group_name" {
  description = "UI CloudWatch log group name"
  value       = aws_cloudwatch_log_group.ui.name
}

output "central_log_group_name" {
  description = "Central CloudWatch log group name"
  value       = aws_cloudwatch_log_group.central.name
}
