output "app_name" {
  description = "CodeDeploy application name"
  value       = aws_codedeploy_app.main.name
}

output "app_id" {
  description = "CodeDeploy application ID"
  value       = aws_codedeploy_app.main.id
}

output "api_deployment_group_name" {
  description = "API deployment group name"
  value       = aws_codedeploy_deployment_group.api.deployment_group_name
}

output "ui_deployment_group_name" {
  description = "UI deployment group name"
  value       = aws_codedeploy_deployment_group.ui.deployment_group_name
}

output "central_deployment_group_name" {
  description = "Central deployment group name"
  value       = aws_codedeploy_deployment_group.central.deployment_group_name
}
