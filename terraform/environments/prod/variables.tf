variable "project_name" {
  description = "Project name"
  type        = string
  default     = "sentinel-v2"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "dev"
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

# Networking
variable "vpc_cidr" {
  description = "VPC CIDR block"
  type        = string
}

variable "availability_zones" {
  description = "Availability zones"
  type        = list(string)
}

variable "public_subnet_cidrs" {
  description = "Public subnet CIDR blocks"
  type        = list(string)
}

variable "private_subnet_cidrs" {
  description = "Private subnet CIDR blocks"
  type        = list(string)
}

# Database
variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
}

variable "db_allocated_storage" {
  description = "Allocated storage in GB"
  type        = number
}

variable "db_max_allocated_storage" {
  description = "Maximum allocated storage for autoscaling"
  type        = number
}

variable "db_name" {
  description = "Database name"
  type        = string
}

variable "db_username" {
  description = "Database master username"
  type        = string
}

variable "db_password" {
  description = "Database master password"
  type        = string
  sensitive   = true
}

variable "db_multi_az" {
  description = "Enable Multi-AZ deployment"
  type        = bool
}

variable "db_backup_retention_period" {
  description = "Backup retention period in days"
  type        = number
}

# Secrets
variable "openai_api_key" {
  description = "OpenAI API key"
  type        = string
  sensitive   = true
}

variable "langgraph_api_key" {
  description = "Langgraph API key"
  type        = string
  sensitive   = true
}

variable "api_secret_key" {
  description = "API secret key for JWT"
  type        = string
  sensitive   = true
}

# ECR
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

# API Service
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
  description = "API minimum tasks for autoscaling"
  type        = number
}

variable "api_max_capacity" {
  description = "API maximum tasks for autoscaling"
  type        = number
}

# UI Service
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
  description = "UI minimum tasks for autoscaling"
  type        = number
}

variable "ui_max_capacity" {
  description = "UI maximum tasks for autoscaling"
  type        = number
}

# Central Service
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
  description = "Central minimum tasks for autoscaling"
  type        = number
}

variable "central_max_capacity" {
  description = "Central maximum tasks for autoscaling"
  type        = number
}

# Route53 & HTTPS Configuration
variable "enable_https" {
  description = "Enable HTTPS with custom domain"
  type        = bool
  default     = false
}

variable "domain_name" {
  description = "Domain name (e.g., sentinel-mas.com)"
  type        = string
  default     = ""
}

variable "subdomain" {
  description = "Subdomain (e.g., 'dev' for dev.sentinel-mas.com, leave empty for root domain)"
  type        = string
  default     = ""
}

variable "subject_alternative_names" {
  description = "Alternative domain names for certificate (e.g., ['*.sentinel-mas.com'])"
  type        = list(string)
  default     = []
}

variable "create_www_redirect" {
  description = "Create www subdomain redirect"
  type        = bool
  default     = false
}
