variable "project_name" {
  description = "Project name"
  type        = string
}

variable "environment" {
  description = "Environment (dev/prod)"
  type        = string
}

variable "cluster_name" {
  description = "ECS cluster name"
  type        = string
}

variable "codedeploy_role_arn" {
  description = "CodeDeploy IAM role ARN"
  type        = string
}

variable "listener_arn" {
  description = "ALB HTTP listener ARN"
  type        = string
}

variable "https_listener_arn" {
  description = "ALB HTTPS listener ARN"
  type        = string
}

# API Service
variable "api_service_name" {
  description = "API service name"
  type        = string
}

variable "api_blue_target_group_name" {
  description = "API blue target group name"
  type        = string
}

variable "api_green_target_group_name" {
  description = "API green target group name"
  type        = string
}

# UI Service
variable "ui_service_name" {
  description = "UI service name"
  type        = string
}

variable "ui_blue_target_group_name" {
  description = "UI blue target group name"
  type        = string
}

variable "ui_green_target_group_name" {
  description = "UI green target group name"
  type        = string
}

# Central Service
variable "central_service_name" {
  description = "Central service name"
  type        = string
}

variable "central_blue_target_group_name" {
  description = "Central blue target group name"
  type        = string
}

variable "central_green_target_group_name" {
  description = "Central green target group name"
  type        = string
}
