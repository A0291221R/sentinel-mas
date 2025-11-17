# Stage 6: Monitoring & Observability Module

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# # CloudWatch Log Groups
# resource "aws_cloudwatch_log_group" "api" {
#   name              = "/ecs/${var.project_name}-${var.environment}-api"
#   retention_in_days = var.log_retention_days
  
#   tags = {
#     Name        = "${var.project_name}-${var.environment}-api-logs"
#     Environment = var.environment
#     Service     = "api"
#   }
# }

# resource "aws_cloudwatch_log_group" "ui" {
#   name              ="/ecs/${var.project_name}-${var.environment}-ui"
#   retention_in_days = var.log_retention_days
  
#   tags = {
#     Name        = "${var.project_name}-${var.environment}-ui-logs"
#     Environment = var.environment
#     Service     = "ui"
#   }
# }

# resource "aws_cloudwatch_log_group" "central" {
#   name              = "/ecs/${var.project_name}-${var.environment}-central"
#   retention_in_days = var.log_retention_days
  
#   tags = {
#     Name        = "${var.project_name}-${var.environment}-central-logs"
#     Environment = var.environment
#     Service     = "central"
#   }
# }


# SNS Topic for Alerts
resource "aws_sns_topic" "alerts" {
  name = "${var.project_name}-${var.environment}-alerts"
  
  tags = {
    Name        = "${var.environment}-alerts"
    Environment = var.environment
  }
}

resource "aws_sns_topic_subscription" "email" {
  count     = length(var.alert_emails)
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = var.alert_emails[count.index]
}

# CloudWatch Dashboard
resource "aws_cloudwatch_dashboard" "main" {
  dashboard_name = "${var.project_name}-${var.environment}"
  
  dashboard_body = jsonencode({
    widgets = [
      # API Service Metrics
      {
        type = "metric"
        properties = {
          metrics = [
            ["AWS/ECS", "CPUUtilization", "ServiceName", var.api_service_name, "ClusterName", var.cluster_name],
            [".", "MemoryUtilization", ".", ".", ".", "."]
          ]
          period = 300
          stat   = "Average"
          region = var.aws_region
          title  = "API - CPU & Memory"
        }
      },
      # UI Service Metrics
      {
        type = "metric"
        properties = {
          metrics = [
            ["AWS/ECS", "CPUUtilization", "ServiceName", var.ui_service_name, "ClusterName", var.cluster_name],
            [".", "MemoryUtilization", ".", ".", ".", "."]
          ]
          period = 300
          stat   = "Average"
          region = var.aws_region
          title  = "UI - CPU & Memory"
        }
      },
      # Central Service Metrics
      {
        type = "metric"
        properties = {
          metrics = [
            ["AWS/ECS", "CPUUtilization", "ServiceName", var.central_service_name, "ClusterName", var.cluster_name],
            [".", "MemoryUtilization", ".", ".", ".", "."]
          ]
          period = 300
          stat   = "Average"
          region = var.aws_region
          title  = "Central - CPU & Memory"
        }
      },
      # ALB Metrics
      {
        type = "metric"
        properties = {
          metrics = [
            ["AWS/ApplicationELB", "TargetResponseTime", "LoadBalancer", var.alb_arn_suffix],
            [".", "RequestCount", ".", "."],
            [".", "HTTPCode_Target_5XX_Count", ".", "."]
          ]
          period = 300
          stat   = "Sum"
          region = var.aws_region
          title  = "ALB - Performance"
        }
      },
      # RDS Metrics
      {
        type = "metric"
        properties = {
          metrics = [
            ["AWS/RDS", "CPUUtilization", "DBInstanceIdentifier", var.db_instance_id],
            [".", "DatabaseConnections", ".", "."],
            [".", "FreeableMemory", ".", "."]
          ]
          period = 300
          stat   = "Average"
          region = var.aws_region
          title  = "RDS - Database Health"
        }
      }
    ]
  })
}

# CloudWatch Alarms - API Service
resource "aws_cloudwatch_metric_alarm" "api_cpu_high" {
  alarm_name          = "${var.environment}-api-cpu-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ECS"
  period              = 300
  statistic           = "Average"
  threshold           = var.cpu_alarm_threshold
  alarm_description   = "API CPU utilization is too high"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  
  dimensions = {
    ServiceName = var.api_service_name
    ClusterName = var.cluster_name
  }
}

resource "aws_cloudwatch_metric_alarm" "api_memory_high" {
  alarm_name          = "${var.environment}-api-memory-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "MemoryUtilization"
  namespace           = "AWS/ECS"
  period              = 300
  statistic           = "Average"
  threshold           = var.memory_alarm_threshold
  alarm_description   = "API memory utilization is too high"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  
  dimensions = {
    ServiceName = var.api_service_name
    ClusterName = var.cluster_name
  }
}

# CloudWatch Alarms - UI Service
resource "aws_cloudwatch_metric_alarm" "ui_cpu_high" {
  alarm_name          = "${var.environment}-ui-cpu-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ECS"
  period              = 300
  statistic           = "Average"
  threshold           = var.cpu_alarm_threshold
  alarm_description   = "UI CPU utilization is too high"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  
  dimensions = {
    ServiceName = var.ui_service_name
    ClusterName = var.cluster_name
  }
}

# CloudWatch Alarms - Central Service
resource "aws_cloudwatch_metric_alarm" "central_cpu_high" {
  alarm_name          = "${var.environment}-central-cpu-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ECS"
  period              = 300
  statistic           = "Average"
  threshold           = var.cpu_alarm_threshold
  alarm_description   = "Central CPU utilization is too high"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  
  dimensions = {
    ServiceName = var.central_service_name
    ClusterName = var.cluster_name
  }
}

# ALB Alarms
resource "aws_cloudwatch_metric_alarm" "alb_5xx_errors" {
  alarm_name          = "${var.environment}-alb-5xx-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "HTTPCode_Target_5XX_Count"
  namespace           = "AWS/ApplicationELB"
  period              = 300
  statistic           = "Sum"
  threshold           = 10
  alarm_description   = "Too many 5XX errors from targets"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  
  dimensions = {
    LoadBalancer = var.alb_arn_suffix
  }
}

resource "aws_cloudwatch_metric_alarm" "alb_response_time" {
  alarm_name          = "${var.environment}-alb-high-response-time"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "TargetResponseTime"
  namespace           = "AWS/ApplicationELB"
  period              = 300
  statistic           = "Average"
  threshold           = 2
  alarm_description   = "ALB response time is too high"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  
  dimensions = {
    LoadBalancer = var.alb_arn_suffix
  }
}

# RDS Alarms
resource "aws_cloudwatch_metric_alarm" "rds_cpu_high" {
  alarm_name          = "${var.environment}-rds-cpu-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "CPUUtilization"
  namespace           = "AWS/RDS"
  period              = 300
  statistic           = "Average"
  threshold           = 80
  alarm_description   = "RDS CPU utilization is too high"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  
  dimensions = {
    DBInstanceIdentifier = var.db_instance_id
  }
}

resource "aws_cloudwatch_metric_alarm" "rds_storage_low" {
  alarm_name          = "${var.environment}-rds-storage-low"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = 1
  metric_name         = "FreeStorageSpace"
  namespace           = "AWS/RDS"
  period              = 300
  statistic           = "Average"
  threshold           = 10737418240  # 10 GB in bytes
  alarm_description   = "RDS free storage is running low"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  
  dimensions = {
    DBInstanceIdentifier = var.db_instance_id
  }
}
