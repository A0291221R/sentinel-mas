variable "project_name" {
  description = "Project name"
  type        = string
}

variable "environment" {
  description = "Environment (dev/prod)"
  type        = string
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "cluster_name" {
  description = "ECS cluster name"
  type        = string
}

variable "alb_arn_suffix" {
  description = "ALB ARN suffix for CloudWatch metrics"
  type        = string
}

variable "db_instance_id" {
  description = "RDS instance identifier"
  type        = string
}

variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 7
}

variable "alert_emails" {
  description = "List of email addresses for alerts"
  type        = list(string)
  default     = []
}

variable "cpu_alarm_threshold" {
  description = "CPU utilization threshold for alarms (%)"
  type        = number
  default     = 80
}

variable "memory_alarm_threshold" {
  description = "Memory utilization threshold for alarms (%)"
  type        = number
  default     = 80
}

variable "ui_service_name" {
  description = "UI service name"
  type        = string
}

variable "api_service_name" {
  description = "API service name"
  type        = string
}

variable "central_service_name" {
  description = "Central service name"
  type        = string
}

