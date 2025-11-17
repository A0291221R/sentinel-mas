# X-Ray Module for Distributed Tracing

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# X-Ray Daemon Log Group
resource "aws_cloudwatch_log_group" "xray_daemon" {
  name              = "/ecs/${var.environment}/xray-daemon"
  retention_in_days = 7
  
  tags = {
    Name        = "${var.environment}-xray-daemon-logs"
    Environment = var.environment
  }
}

# X-Ray Sampling Rule
resource "aws_xray_sampling_rule" "main" {
  rule_name      = "${var.project_name}-${var.environment}"
  priority       = 1000
  version        = 1
  reservoir_size = 1
  fixed_rate     = 0.05  # Sample 5% of requests
  url_path       = "*"
  host           = "*"
  http_method    = "*"
  service_type   = "*"
  service_name   = "*"
  resource_arn   = "*"
  
  attributes = {
    Environment = var.environment
  }
}

# X-Ray High Priority Sampling (for errors and slow requests)
resource "aws_xray_sampling_rule" "errors" {
  rule_name      = "${var.project_name}-${var.environment}-errors"
  priority       = 100
  version        = 1
  reservoir_size = 1
  fixed_rate     = 1.0  # Sample 100% of errors
  url_path       = "*"
  host           = "*"
  http_method    = "*"
  service_type   = "*"
  service_name   = "*"
  resource_arn   = "*"
  
  attributes = {
    Environment = var.environment
    Type        = "error"
  }
}

# IAM Policy for X-Ray
data "aws_iam_policy_document" "xray" {
  statement {
    effect = "Allow"
    actions = [
      "xray:PutTraceSegments",
      "xray:PutTelemetryRecords",
      "xray:GetSamplingRules",
      "xray:GetSamplingTargets",
      "xray:GetSamplingStatisticSummaries"
    ]
    resources = ["*"]
  }
}

resource "aws_iam_policy" "xray" {
  name        = "${var.project_name}-${var.environment}-xray"
  description = "Allow ECS tasks to write to X-Ray"
  policy      = data.aws_iam_policy_document.xray.json
}

# Attach X-Ray policy to task execution role
resource "aws_iam_role_policy_attachment" "xray_api" {
  role       = var.api_task_role_name
  policy_arn = aws_iam_policy.xray.arn
}

resource "aws_iam_role_policy_attachment" "xray_ui" {
  role       = var.ui_task_role_name
  policy_arn = aws_iam_policy.xray.arn
}

resource "aws_iam_role_policy_attachment" "xray_central" {
  role       = var.central_task_role_name
  policy_arn = aws_iam_policy.xray.arn
}

# X-Ray Group for filtering traces
resource "aws_xray_group" "api" {
  group_name        = "${var.project_name}-${var.environment}-api"
  filter_expression = "service(\"${var.project_name}-${var.environment}-api\")"
  
  insights_configuration {
    insights_enabled      = true
    notifications_enabled = false
  }
}

resource "aws_xray_group" "central" {
  group_name        = "${var.project_name}-${var.environment}-central"
  filter_expression = "service(\"${var.project_name}-${var.environment}-central\")"
  
  insights_configuration {
    insights_enabled      = true
    notifications_enabled = false
  }
}
