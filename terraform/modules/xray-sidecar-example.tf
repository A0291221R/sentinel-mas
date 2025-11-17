# X-Ray Daemon Sidecar Container Definition
# Add this to your ECS task definitions

locals {
  xray_container_definition = {
    name      = "xray-daemon"
    image     = "public.ecr.aws/xray/aws-xray-daemon:latest"
    cpu       = 32
    memory    = 256
    essential = true
    
    portMappings = [
      {
        containerPort = 2000
        protocol      = "udp"
        name          = "xray"
      }
    ]
    
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = "/ecs/${var.environment}/xray-daemon"
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "xray"
      }
    }
  }
}

# Example: Updated API Task Definition with X-Ray
resource "aws_ecs_task_definition" "api_with_xray" {
  family                   = "${var.environment}-sentinel-mas-api"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = 512
  memory                   = 1024
  execution_role_arn       = var.execution_role_arn
  task_role_arn            = var.task_role_arn

  container_definitions = jsonencode([
    {
      name      = "api"
      image     = "${var.ecr_repository_url}:latest"
      cpu       = 480
      memory    = 768
      essential = true
      
      environment = [
        {
          name  = "AWS_XRAY_DAEMON_ADDRESS"
          value = "xray-daemon:2000"
        },
        {
          name  = "AWS_XRAY_TRACING_NAME"
          value = "${var.environment}-sentinel-mas-api"
        }
      ]
      
      portMappings = [
        {
          containerPort = 3000
          protocol      = "tcp"
        }
      ]
      
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = "/ecs/${var.environment}/sentinel-mas-api"
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "api"
        }
      }
    },
    local.xray_container_definition
  ])
}

# CloudWatch Log Group for X-Ray Daemon
resource "aws_cloudwatch_log_group" "xray" {
  name              = "/ecs/${var.environment}/xray-daemon"
  retention_in_days = 7
}
