output "alb_dns_name" {
  description = "ALB DNS name - use this to access your application"
  value       = module.alb.alb_dns_name
}

output "alb_url" {
  description = "Application URL"
  value       = "http://${module.alb.alb_dns_name}"
}

output "api_url" {
  description = "API endpoint URL"
  value       = "http://${module.alb.alb_dns_name}/api"
}

output "ui_url" {
  description = "UI endpoint URL"
  value       = "http://${module.alb.alb_dns_name}"
}

output "central_url" {
  description = "Central endpoint URL"
  value       = "http://${module.alb.alb_dns_name}/central"
}

output "vpc_id" {
  description = "VPC ID"
  value       = module.networking.vpc_id
}

output "ecs_cluster_name" {
  description = "ECS cluster name"
  value       = module.ecs.cluster_name
}

output "rds_endpoint" {
  description = "RDS endpoint"
  value       = module.rds.db_endpoint
  sensitive   = true
}

output "codedeploy_app_name" {
  description = "CodeDeploy application name"
  value       = module.codedeploy.app_name
}

output "api_service_name" {
  description = "API ECS service name"
  value       = module.ecs.api_service_name
}

output "ui_service_name" {
  description = "UI ECS service name"
  value       = module.ecs.ui_service_name
}

output "central_service_name" {
  description = "Central ECS service name"
  value       = module.ecs.central_service_name
}

output "domain_name" {
  description = "Custom domain name (if HTTPS enabled)"
  value       = var.enable_https ? module.route53[0].domain_name : "Not configured"
}

output "https_url" {
  description = "HTTPS URL (if HTTPS enabled)"
  value       = var.enable_https ? "https://${module.route53[0].domain_name}" : "HTTPS not enabled"
}
