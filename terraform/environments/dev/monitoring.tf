module "monitoring" {
  source = "../../modules/monitoring"

  project_name   = var.project_name
  environment    = var.environment
  aws_region     = var.aws_region

  cluster_name   = module.ecs.cluster_name
  alb_arn_suffix = module.alb.alb_arn_suffix
  db_instance_id = module.rds.db_instance_id

  api_service_name = module.ecs.api_service_name
  ui_service_name  = module.ecs.ui_service_name
  central_service_name = module.ecs.central_service_name

  log_retention_days = 7  # 7 days for dev, 30 for prod

  alert_emails = [
    "chekeong82@gmail.com",
    "E1330360@u.nus.edu"
  ]

  cpu_alarm_threshold    = 80
  memory_alarm_threshold = 80
}

module "xray" {
  source = "../../modules/xray"

  project_name         = var.project_name
  environment          = var.environment

  api_task_role_name     = module.iam.ecs_task_role_name
  ui_task_role_name      = module.iam.ecs_task_role_name
  central_task_role_name =  module.iam.ecs_task_role_name
}

output "dashboard_url" {
  value = "https://console.aws.amazon.com/cloudwatch/home?region=${var.aws_region}#dashboards:name=${module.monitoring.dashboard_name}"
}

output "xray_console_url" {
  value = "https://console.aws.amazon.com/xray/home?region=${var.aws_region}#/service-map"
}