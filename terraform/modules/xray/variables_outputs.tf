# Variables
variable "project_name" {
  description = "Project name"
  type        = string
}

variable "environment" {
  description = "Environment (dev/prod)"
  type        = string
}

variable "api_task_role_name" {
  description = "API ECS task role name"
  type        = string
}

variable "ui_task_role_name" {
  description = "UI ECS task role name"
  type        = string
}

variable "central_task_role_name" {
  description = "Central ECS task role name"
  type        = string
}

# Outputs
output "xray_policy_arn" {
  description = "X-Ray IAM policy ARN"
  value       = aws_iam_policy.xray.arn
}

output "sampling_rule_name" {
  description = "X-Ray sampling rule name"
  value       = aws_xray_sampling_rule.main.rule_name
}
