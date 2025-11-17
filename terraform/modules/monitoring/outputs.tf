# output "log_group_api_name" {
#   description = "API log group name"
#   value       = aws_cloudwatch_log_group.api.name
# }

# output "log_group_ui_name" {
#   description = "UI log group name"
#   value       = aws_cloudwatch_log_group.ui.name
# }

# output "log_group_central_name" {
#   description = "Central log group name"
#   value       = aws_cloudwatch_log_group.central.name
# }

output "sns_topic_arn" {
  description = "SNS topic ARN for alerts"
  value       = aws_sns_topic.alerts.arn
}

output "dashboard_name" {
  description = "CloudWatch dashboard name"
  value       = aws_cloudwatch_dashboard.main.dashboard_name
}
