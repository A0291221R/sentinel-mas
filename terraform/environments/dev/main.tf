terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Optional: Configure S3 backend for state management
  # backend "s3" {
  #   bucket         = "your-terraform-state-bucket"
  #   key            = "sentinel-mas/dev/terraform.tfstate"
  #   region         = "us-east-1"
  #   dynamodb_table = "terraform-state-lock"
  #   encrypt        = true
  # }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}

# Data sources
data "aws_caller_identity" "current" {}

# Networking Module
module "networking" {
  source = "../../modules/networking"

  project_name         = var.project_name
  environment          = var.environment
  vpc_cidr             = var.vpc_cidr
  availability_zones   = var.availability_zones
  public_subnet_cidrs  = var.public_subnet_cidrs
  private_subnet_cidrs = var.private_subnet_cidrs
}

# Security Groups Module
module "security_groups" {
  source = "../../modules/security-groups"

  project_name = var.project_name
  environment  = var.environment
  vpc_id       = module.networking.vpc_id
}

# IAM Module
module "iam" {
  source = "../../modules/iam"

  project_name   = var.project_name
  environment    = var.environment
  aws_region     = var.aws_region
  aws_account_id = data.aws_caller_identity.current.account_id
}

# RDS Module
module "rds" {
  source = "../../modules/rds"

  project_name               = var.project_name
  environment                = var.environment
  private_subnet_ids         = module.networking.private_subnet_ids
  rds_security_group_id      = module.security_groups.rds_security_group_id
  db_instance_class          = var.db_instance_class
  db_allocated_storage       = var.db_allocated_storage
  db_max_allocated_storage   = var.db_max_allocated_storage
  db_name                    = var.db_name
  db_username                = var.db_username
  db_password                = var.db_password
  db_multi_az                = var.db_multi_az
  db_backup_retention_period = var.db_backup_retention_period
}

# ALB Module
module "alb" {
  source = "../../modules/alb"

  project_name          = var.project_name
  environment           = var.environment
  vpc_id                = module.networking.vpc_id
  public_subnet_ids     = module.networking.public_subnet_ids
  alb_security_group_id = module.security_groups.alb_security_group_id
  
  enable_https          = var.enable_https
  certificate_arn       = var.enable_https ? module.acm[0].certificate_arn : ""
}

# ACM Module (optional - only if HTTPS enabled)
module "acm" {
  count  = var.enable_https ? 1 : 0
  source = "../../modules/acm"

  project_name              = var.project_name
  environment               = var.environment
  domain_name               = var.enable_https ? (var.subdomain != "" ? "${var.subdomain}.${var.domain_name}" : var.domain_name) : ""
  subject_alternative_names = var.enable_https ? var.subject_alternative_names : []
  hosted_zone_id            = var.enable_https ? data.aws_route53_zone.main[0].zone_id : ""
}

# Route53 Zone Data (optional - only if HTTPS enabled)
data "aws_route53_zone" "main" {
  count        = var.enable_https ? 1 : 0
  name         = var.domain_name
  private_zone = false
}

# Route53 Module (optional - only if HTTPS enabled)
module "route53" {
  count  = var.enable_https ? 1 : 0
  source = "../../modules/route53"

  domain_name          = var.domain_name
  subdomain            = var.subdomain
  alb_dns_name         = module.alb.alb_dns_name
  alb_zone_id          = module.alb.alb_zone_id
  create_www_redirect  = var.create_www_redirect

  depends_on = [module.alb]
}

# Create additional secrets for API
resource "aws_secretsmanager_secret" "openai_api_key" {
  name = "${var.environment}/${var.project_name}/openai-key"

  tags = {
    Name        = "${var.project_name}-${var.environment}-openai-key"
    Environment = var.environment
  }
  recovery_window_in_days = 0
  lifecycle {
    prevent_destroy = false
  }
}

resource "aws_secretsmanager_secret_version" "openai_api_key" {
  secret_id     = aws_secretsmanager_secret.openai_api_key.id
  secret_string = var.openai_api_key
}

resource "aws_secretsmanager_secret" "langgraph_api_key" {
  name = "${var.environment}/${var.project_name}/langgraph-key"

  tags = {
    Name        = "${var.project_name}-${var.environment}-langgraph-key"
    Environment = var.environment
  }
  recovery_window_in_days = 0
  lifecycle {
    prevent_destroy = false
  }
}

resource "aws_secretsmanager_secret_version" "langgraph_api_key" {
  secret_id     = aws_secretsmanager_secret.langgraph_api_key.id
  secret_string = var.langgraph_api_key
}

# For api-service
resource "aws_secretsmanager_secret" "sentinel_db_url" {
  name = "${var.environment}/${var.project_name}/sentinel-db-url"
  tags = {
    Name        = "${var.project_name}-${var.environment}-sentinel-db-url"
    Environment = var.environment
  }
  recovery_window_in_days = 0
  lifecycle {
    prevent_destroy = false
  }
}

resource "aws_secretsmanager_secret_version" "sentinel_db_url" {
  secret_id     = aws_secretsmanager_secret.sentinel_db_url.id
  secret_string = "postgresql://${var.db_username}:${var.db_password}@${module.rds.db_address}:${module.rds.db_port}/${module.rds.db_name}"
}

# For sentinel-Central
resource "aws_secretsmanager_secret" "db_url" {
  name = "${var.environment}/${var.project_name}/db-url"
  tags = {
    Name        = "${var.project_name}-${var.environment}-db-url"
    Environment = var.environment
  }
  recovery_window_in_days = 0
  lifecycle {
    prevent_destroy = false
  }
}

resource "aws_secretsmanager_secret_version" "db_url" {
  secret_id     = aws_secretsmanager_secret.db_url.id
  secret_string = "postgresql+asyncpg://${var.db_username}:${var.db_password}@${module.rds.db_address}:${module.rds.db_port}/${module.rds.db_name}"
}

resource "aws_secretsmanager_secret" "api_secret_key" {
  name = "${var.environment}/${var.project_name}/api-secret"

  tags = {
    Name        = "${var.project_name}-${var.environment}-api-secret"
    Environment = var.environment
  }
  recovery_window_in_days = 0
  lifecycle {
    prevent_destroy = false
  }
}

resource "aws_secretsmanager_secret_version" "api_secret_key" {
  secret_id     = aws_secretsmanager_secret.api_secret_key.id
  secret_string = var.api_secret_key
}

locals {
  allowed_origins = ["http://${module.alb.alb_dns_name}","http://localhost:8000", "http://localhost:8080"]
}

# ECS Module
module "ecs" {
  source = "../../modules/ecs"

  project_name    = var.project_name
  environment     = var.environment
  aws_region      = var.aws_region
  private_subnet_ids = module.networking.private_subnet_ids

  ecs_task_execution_role_arn = module.iam.ecs_task_execution_role_arn
  ecs_task_role_arn           = module.iam.ecs_task_role_arn

  ecs_api_security_group_id     = module.security_groups.ecs_api_security_group_id
  ecs_ui_security_group_id      = module.security_groups.ecs_ui_security_group_id
  ecs_central_security_group_id = module.security_groups.ecs_central_security_group_id

  # Listener dependency  
  alb_listener = module.alb.listener
  
  # Add listener rule dependencies
  alb_listener_rule_api     = module.alb.listener_rule_api
  alb_listener_rule_ui      = module.alb.listener_rule_ui
  alb_listener_rule_central = module.alb.listener_rule_central

  # Database
  db_address              = module.rds.db_address
  db_port                 = module.rds.db_port
  db_name                 = module.rds.db_name
  db_password_secret_arn  = module.rds.db_password_secret_arn

  # Secrets
  langgraph_api_key            = var.langgraph_api_key
  openai_api_key_secret_arn = aws_secretsmanager_secret.openai_api_key.arn
  langgraph_api_key_secret_arn = aws_secretsmanager_secret.langgraph_api_key.arn
  sentinel_db_url_secret_arn = aws_secretsmanager_secret.sentinel_db_url.arn
  db_url_secret_arn = aws_secretsmanager_secret.db_url.arn
  api_secret_key_secret_arn = aws_secretsmanager_secret.api_secret_key.arn

  # Target Groups
  api_blue_target_group_arn     = module.alb.api_blue_target_group_arn
  ui_blue_target_group_arn      = module.alb.ui_blue_target_group_arn
  central_blue_target_group_arn = module.alb.central_blue_target_group_arn

  # ECR
  ecr_repository_url_api     = var.ecr_repository_url_api
  ecr_repository_url_ui      = var.ecr_repository_url_ui
  ecr_repository_url_central = var.ecr_repository_url_central

  # Service Configuration
  api_cpu            = var.api_cpu
  api_memory         = var.api_memory
  api_desired_count  = var.api_desired_count
  api_min_capacity   = var.api_min_capacity
  api_max_capacity   = var.api_max_capacity

  ui_cpu            = var.ui_cpu
  ui_memory         = var.ui_memory
  ui_desired_count  = var.ui_desired_count
  ui_min_capacity   = var.ui_min_capacity
  ui_max_capacity   = var.ui_max_capacity

  central_cpu            = var.central_cpu
  central_memory         = var.central_memory
  central_desired_count  = var.central_desired_count
  central_min_capacity   = var.central_min_capacity
  central_max_capacity   = var.central_max_capacity

  api_url = "http://${module.alb.alb_dns_name}/api"
  central_url = "http://${module.alb.alb_dns_name}/tracking"
  allowed_origins = jsonencode(local.allowed_origins) 
}

# CodeDeploy Module
module "codedeploy" {
  source = "../../modules/codedeploy"

  project_name         = var.project_name
  environment          = var.environment
  cluster_name         = module.ecs.cluster_name
  codedeploy_role_arn  = module.iam.codedeploy_role_arn
  # listener_arn         = module.alb.listener_arn
  # IMPORTANT:
  # - No cert: HTTP listener (port 80) is used for traffic switching
  # - Cert present: HTTPS listener (port 443) is used for traffic switching
  listener_arn = (
    module.alb.certificate_arn != ""
    ? module.alb.https_listener_arn
    : module.alb.listener_arn
  )
  https_listener_arn = module.alb.https_listener_arn

  # API
  api_service_name            = module.ecs.api_service_name
  api_blue_target_group_name  = module.alb.api_blue_target_group_name
  api_green_target_group_name = module.alb.api_green_target_group_name

  # UI
  ui_service_name            = module.ecs.ui_service_name
  ui_blue_target_group_name  = module.alb.ui_blue_target_group_name
  ui_green_target_group_name = module.alb.ui_green_target_group_name

  # Central
  central_service_name            = module.ecs.central_service_name
  central_blue_target_group_name  = module.alb.central_blue_target_group_name
  central_green_target_group_name = module.alb.central_green_target_group_name
}
