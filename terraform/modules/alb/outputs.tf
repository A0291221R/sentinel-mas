output "alb_id" {
  description = "ALB ID"
  value       = aws_lb.main.id
}

output "alb_arn_suffix" {
  description = "ARN suffix of the ALB for use with CloudWatch metrics"
  value       = aws_lb.main.arn_suffix
}

output "alb_arn" {
  description = "ALB ARN"
  value       = aws_lb.main.arn
}

output "alb_dns_name" {
  description = "ALB DNS name"
  value       = aws_lb.main.dns_name
}

output "alb_zone_id" {
  description = "ALB zone ID"
  value       = aws_lb.main.zone_id
}

output "listener_arn" {
  description = "HTTP listener ARN"
  value       = aws_lb_listener.http.arn
}

output "https_listener_arn" {
  description = "HTTPS listener ARN (if certificate provided)"
  value       = var.certificate_arn != "" ? aws_lb_listener.https[0].arn : null
}

# API Target Groups
output "api_blue_target_group_arn" {
  description = "API blue target group ARN"
  value       = aws_lb_target_group.api_blue.arn
}

output "api_blue_target_group_name" {
  description = "API blue target group name"
  value       = aws_lb_target_group.api_blue.name
}

output "api_green_target_group_arn" {
  description = "API green target group ARN"
  value       = aws_lb_target_group.api_green.arn
}

output "api_green_target_group_name" {
  description = "API green target group name"
  value       = aws_lb_target_group.api_green.name
}

# UI Target Groups
output "ui_blue_target_group_arn" {
  description = "UI blue target group ARN"
  value       = aws_lb_target_group.ui_blue.arn
}

output "ui_blue_target_group_name" {
  description = "UI blue target group name"
  value       = aws_lb_target_group.ui_blue.name
}

output "ui_green_target_group_arn" {
  description = "UI green target group ARN"
  value       = aws_lb_target_group.ui_green.arn
}

output "ui_green_target_group_name" {
  description = "UI green target group name"
  value       = aws_lb_target_group.ui_green.name
}

# Central Target Groups
output "central_blue_target_group_arn" {
  description = "Central blue target group ARN"
  value       = aws_lb_target_group.central_blue.arn
}

output "central_blue_target_group_name" {
  description = "Central blue target group name"
  value       = aws_lb_target_group.central_blue.name
}

output "central_green_target_group_arn" {
  description = "Central green target group ARN"
  value       = aws_lb_target_group.central_green.arn
}

output "central_green_target_group_name" {
  description = "Central green target group name"
  value       = aws_lb_target_group.central_green.name
}

output "certificate_arn" {
  value = var.certificate_arn
}

output "listener" {
  description = "ALB listener for ECS dependency"
  value       = aws_lb_listener.http
}

# Add outputs for listener rules:
output "listener_rule_api" {
  description = "Listener rule for API service"
  value       = aws_lb_listener_rule.api_http  # Use your actual resource name
}

output "listener_rule_ui" {
  description = "Listener rule for UI service"
  value       = aws_lb_listener_rule.ui_http
}

output "listener_rule_central" {
  description = "Listener rule for Central service"
  value       = aws_lb_listener_rule.central_http
}