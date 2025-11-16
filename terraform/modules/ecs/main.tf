# ============================================
# ECS Cluster
# ============================================
resource "aws_ecs_cluster" "main" {
  name = "${var.project_name}-${var.environment}-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-cluster"
    Environment = var.environment
  }
}

# ============================================
# CloudWatch Log Groups
# ============================================
resource "aws_cloudwatch_log_group" "api" {
  name              = "/ecs/${var.project_name}-${var.environment}-api"
  retention_in_days = var.log_retention_days

  tags = {
    Name        = "${var.project_name}-${var.environment}-api-logs"
    Environment = var.environment
  }
}

resource "aws_cloudwatch_log_group" "ui" {
  name              = "/ecs/${var.project_name}-${var.environment}-ui"
  retention_in_days = var.log_retention_days

  tags = {
    Name        = "${var.project_name}-${var.environment}-ui-logs"
    Environment = var.environment
  }
}

resource "aws_cloudwatch_log_group" "central" {
  name              = "/ecs/${var.project_name}-${var.environment}-central"
  retention_in_days = var.log_retention_days

  tags = {
    Name        = "${var.project_name}-${var.environment}-central-logs"
    Environment = var.environment
  }
}

# ============================================
# Task Definition - API Service
# ============================================
resource "aws_ecs_task_definition" "api" {
  family                   = "${var.project_name}-${var.environment}-api"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = var.api_cpu
  memory                   = var.api_memory
  execution_role_arn       = var.ecs_task_execution_role_arn
  task_role_arn            = var.ecs_task_role_arn

  container_definitions = jsonencode([
    {
      name  = "api"
      image = "${var.ecr_repository_url_api}:${var.api_image_tag}"

      portMappings = [
        {
          containerPort = 8000
          protocol      = "tcp"
        }
      ]

      environment = [
        {
            "name": "ALLOWED_ORIGINS",
            "value": var.allowed_origins
        },
        {
            "name": "LANGCHAIN_PROJECT",
            "value": "sentinel-mas"
        },
        {
            "name": "LANGSMITH_TRACING",
            "value": "true"
        },
        {
          name  = "ENVIRONMENT"
          value = var.environment
        },
        # {
        #   name  = "ENVIRONMENT"
        #   value = "test"
        # },
       {
          "name": "SENTINEL_CENTRAL_URL",
          "value": var.central_url
        },
        {
            "name": "OPENAI_MODEL",
            "value": "gpt-4o-mini"
        },
        {
            "name": "LOG_LEVEL",
            "value": "INFO"
        }
      ]

      secrets = [
        {
          name      = "LANGSMITH_API_KEY"
          valueFrom = var.langgraph_api_key_secret_arn
        },
        {
          name      = "OPENAI_API_KEY"
          valueFrom = var.openai_api_key_secret_arn
        },
        {
          name      = "SECRET_KEY"
          valueFrom = var.api_secret_key_secret_arn
        },
         {
          name      = "SENTINEL_DB_URL"
          valueFrom = var.sentinel_db_url_secret_arn
        },
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.api.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "ecs"
        }
      }

      healthCheck = {
        command     = ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"]
        interval    = 30
        timeout     = 5
        retries     = 3
        startPeriod = 60
      }
    }
  ])

  tags = {
    Name        = "${var.project_name}-${var.environment}-api-task"
    Environment = var.environment
  }
}

# ============================================
# Task Definition - UI Service
# ============================================
resource "aws_ecs_task_definition" "ui" {
  family                   = "${var.project_name}-${var.environment}-ui"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = var.ui_cpu
  memory                   = var.ui_memory
  execution_role_arn       = var.ecs_task_execution_role_arn
  task_role_arn            = var.ecs_task_role_arn

  container_definitions = jsonencode([
    {
      name  = "ui"
      image = "${var.ecr_repository_url_ui}:${var.ui_image_tag}"

      portMappings = [
        {
          containerPort = 80
          protocol      = "tcp"
        }
      ]

      environment = [
        {
          name  = "ENVIRONMENT"
          value = var.environment
        },
        # {
        #     "name": "ENVIRONMENT",
        #     "value": "production"
        # },
        {
          name  = "TRACKING_API_URL"
          value = var.central_url
        },
        {
          name  = "API_URL"
          value = var.api_url
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.ui.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "ecs"
        }
      }

      healthCheck = {
        command     = ["CMD-SHELL", "curl -f http://localhost/ || exit 1"]
        interval    = 30
        timeout     = 5
        retries     = 3
        startPeriod = 60
      }
    }
  ])

  tags = {
    Name        = "${var.project_name}-${var.environment}-ui-task"
    Environment = var.environment
  }
}

# ============================================
# Task Definition - Central Service
# ============================================
resource "aws_ecs_task_definition" "central" {
  family                   = "${var.project_name}-${var.environment}-central"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = var.central_cpu
  memory                   = var.central_memory
  execution_role_arn       = var.ecs_task_execution_role_arn
  task_role_arn            = var.ecs_task_role_arn

  container_definitions = jsonencode([
    {
      name  = "central"
      image = "${var.ecr_repository_url_central}:${var.central_image_tag}"

      portMappings = [
        {
          containerPort = 8100
          protocol      = "tcp"
        }
      ]

      environment = [
        {
          name  = "ENVIRONMENT"
          value = var.environment
        },
      ]

      secrets = [
        {
          name      = "DB_URL"
          valueFrom = var.db_url_secret_arn
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.central.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "ecs"
        }
      }

      healthCheck = {
        command     = ["CMD-SHELL", "curl -f http://localhost:8100/healthz || exit 1"]
        interval    = 30
        timeout     = 5
        retries     = 3
        startPeriod = 60
      }
    }
  ])

  tags = {
    Name        = "${var.project_name}-${var.environment}-central-task"
    Environment = var.environment
  }
}

# ============================================
# ECS Service - API
# ============================================
resource "aws_ecs_service" "api" {
  name            = "${var.project_name}-${var.environment}-api-service"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.api.arn
  desired_count   = var.api_desired_count
  launch_type     = "FARGATE"

  deployment_controller {
    type = "CODE_DEPLOY"
  }

  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [var.ecs_api_security_group_id]
    assign_public_ip = true
  }

  load_balancer {
    target_group_arn = var.api_blue_target_group_arn
    container_name   = "api"
    container_port   = 8000
  }

  depends_on = [var.alb_listener, var.alb_listener_rule_api]

  lifecycle {
    ignore_changes = [
      load_balancer,  # CodeDeploy switches between blue/green
      # network_configuration,
      desired_count,
      task_definition # CodeDeploy updates this during deployments
    ]
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-api-service"
    Environment = var.environment
  }
}

# ============================================
# ECS Service - UI
# ============================================
resource "aws_ecs_service" "ui" {
  name            = "${var.project_name}-${var.environment}-ui-service"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.ui.arn
  desired_count   = var.ui_desired_count
  launch_type     = "FARGATE"

  deployment_controller {
    type = "CODE_DEPLOY"
  }

  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [var.ecs_ui_security_group_id]
    assign_public_ip = true
  }

  load_balancer {
    target_group_arn = var.ui_blue_target_group_arn
    container_name   = "ui"
    container_port   = 80
  }

  depends_on = [var.alb_listener, var.alb_listener_rule_ui]

  lifecycle {
    ignore_changes = [
      load_balancer,  # CodeDeploy switches between blue/green
      # network_configuration,
      desired_count,
      task_definition # CodeDeploy updates this during deployments
    ]
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-ui-service"
    Environment = var.environment
  }
}

# ============================================
# ECS Service - Central
# ============================================
resource "aws_ecs_service" "central" {
  name            = "${var.project_name}-${var.environment}-central-service"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.central.arn
  desired_count   = var.central_desired_count
  launch_type     = "FARGATE"

  deployment_controller {
    type = "CODE_DEPLOY"
  }

  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [var.ecs_central_security_group_id]
    assign_public_ip = true
  }

  load_balancer {
    target_group_arn = var.central_blue_target_group_arn
    container_name   = "central"
    container_port   = 8100
  }

  depends_on = [var.alb_listener, var.alb_listener_rule_central]

  lifecycle {
    ignore_changes = [
      load_balancer,  # CodeDeploy switches between blue/green
      # network_configuration,
      desired_count,
      task_definition # CodeDeploy updates this during deployments
    ]
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-central-service"
    Environment = var.environment
  }
}

# ============================================
# Auto Scaling - API Service
# ============================================
resource "aws_appautoscaling_target" "api" {
  max_capacity       = var.api_max_capacity
  min_capacity       = var.api_min_capacity
  resource_id        = "service/${aws_ecs_cluster.main.name}/${aws_ecs_service.api.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

resource "aws_appautoscaling_policy" "api_cpu" {
  name               = "${var.project_name}-${var.environment}-api-cpu-scaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.api.resource_id
  scalable_dimension = aws_appautoscaling_target.api.scalable_dimension
  service_namespace  = aws_appautoscaling_target.api.service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
    target_value = 70.0
  }
}

# ============================================
# Auto Scaling - UI Service
# ============================================
resource "aws_appautoscaling_target" "ui" {
  max_capacity       = var.ui_max_capacity
  min_capacity       = var.ui_min_capacity
  resource_id        = "service/${aws_ecs_cluster.main.name}/${aws_ecs_service.ui.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

resource "aws_appautoscaling_policy" "ui_cpu" {
  name               = "${var.project_name}-${var.environment}-ui-cpu-scaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.ui.resource_id
  scalable_dimension = aws_appautoscaling_target.ui.scalable_dimension
  service_namespace  = aws_appautoscaling_target.ui.service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
    target_value = 70.0
  }
}

# ============================================
# Auto Scaling - Central Service
# ============================================
resource "aws_appautoscaling_target" "central" {
  max_capacity       = var.central_max_capacity
  min_capacity       = var.central_min_capacity
  resource_id        = "service/${aws_ecs_cluster.main.name}/${aws_ecs_service.central.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

resource "aws_appautoscaling_policy" "central_cpu" {
  name               = "${var.project_name}-${var.environment}-central-cpu-scaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.central.resource_id
  scalable_dimension = aws_appautoscaling_target.central.scalable_dimension
  service_namespace  = aws_appautoscaling_target.central.service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
    target_value = 70.0
  }
}
