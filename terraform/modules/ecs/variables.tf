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
}

variable "private_subnet_ids" {
  description = "Private subnet IDs"
  type        = list(string)
}

variable "ecs_task_execution_role_arn" {
  description = "ECS task execution role ARN"
  type        = string
}

variable "ecs_task_role_arn" {
  description = "ECS task role ARN"
  type        = string
}

variable "ecs_api_security_group_id" {
  description = "ECS API security group ID"
  type        = string
}

variable "ecs_ui_security_group_id" {
  description = "ECS UI security group ID"
  type        = string
}

variable "ecs_central_security_group_id" {
  description = "ECS Central security group ID"
  type        = string
}

# Database
variable "db_address" {
  description = "Database address"
  type        = string
}

variable "db_port" {
  description = "Database port"
  type        = number
}

variable "db_name" {
  description = "Database name"
  type        = string
}

variable "central_url" {
  description = "Sentinel central url"
  type        = string
}

variable "db_password_secret_arn" {
  description = "Database password secret ARN"
  type        = string
}

# Secrets
variable "openai_api_key_secret_arn" {
  description = "OpenAI API key secret ARN"
  type        = string
}

variable "langgraph_api_key_secret_arn" {
  description = "Langgraph API key secret ARN"
  type        = string
}

variable "langgraph_api_key" {
  description = "Langgraph API key secret ARN"
  type        = string
}

variable "db_url_secret_arn" {
  description = "db url secret ARN"
  type        = string
}

variable "sentinel_db_url_secret_arn" {
  description = "Sentinel db url secret ARN"
  type        = string
}

variable "api_secret_key_secret_arn" {
  description = "API secret key secret ARN"
  type        = string
}

# Target Groups
variable "api_blue_target_group_arn" {
  description = "API blue target group ARN"
  type        = string
}

variable "ui_blue_target_group_arn" {
  description = "UI blue target group ARN"
  type        = string
}

variable "central_blue_target_group_arn" {
  description = "Central blue target group ARN"
  type        = string
}

# ECR Repositories
variable "ecr_repository_url_api" {
  description = "ECR repository URL for API"
  type        = string
}

variable "ecr_repository_url_ui" {
  description = "ECR repository URL for UI"
  type        = string
}

variable "ecr_repository_url_central" {
  description = "ECR repository URL for Central"
  type        = string
}

# Image Tags
variable "api_image_tag" {
  description = "API image tag"
  type        = string
  default     = "latest"
}

variable "ui_image_tag" {
  description = "UI image tag"
  type        = string
  default     = "latest"
}

variable "central_image_tag" {
  description = "Central image tag"
  type        = string
  default     = "latest"
}

# API Service Configuration
variable "api_cpu" {
  description = "API task CPU"
  type        = number
}

variable "api_memory" {
  description = "API task memory"
  type        = number
}

variable "api_desired_count" {
  description = "API desired task count"
  type        = number
}

variable "api_min_capacity" {
  description = "API minimum task count for autoscaling"
  type        = number
}

variable "api_max_capacity" {
  description = "API maximum task count for autoscaling"
  type        = number
}

# UI Service Configuration
variable "ui_cpu" {
  description = "UI task CPU"
  type        = number
}

variable "ui_memory" {
  description = "UI task memory"
  type        = number
}

variable "ui_desired_count" {
  description = "UI desired task count"
  type        = number
}

variable "ui_min_capacity" {
  description = "UI minimum task count for autoscaling"
  type        = number
}

variable "ui_max_capacity" {
  description = "UI maximum task count for autoscaling"
  type        = number
}

# Central Service Configuration
variable "central_cpu" {
  description = "Central task CPU"
  type        = number
}

variable "central_memory" {
  description = "Central task memory"
  type        = number
}

variable "central_desired_count" {
  description = "Central desired task count"
  type        = number
}

variable "central_min_capacity" {
  description = "Central minimum task count for autoscaling"
  type        = number
}

variable "central_max_capacity" {
  description = "Central maximum task count for autoscaling"
  type        = number
}

# Other
variable "api_url" {
  description = "API URL for UI"
  type        = string
}

variable "allowed_origins" {
  description = "Comma-separated CORS allowed origins"
  type        = string
}

variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 30
}
