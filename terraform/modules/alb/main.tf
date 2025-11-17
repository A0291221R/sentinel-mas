# ============================================
# Application Load Balancer
# ============================================
resource "aws_lb" "main" {
  name               = "${var.project_name}-${var.environment}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [var.alb_security_group_id]
  subnets            = var.public_subnet_ids

  enable_deletion_protection = var.environment == "prod" ? true : false
  enable_http2              = true
  enable_cross_zone_load_balancing = true

  tags = {
    Name        = "${var.project_name}-${var.environment}-alb"
    Environment = var.environment
  }
}

# ============================================
# Target Groups - API (Blue/Green)
# ============================================
resource "aws_lb_target_group" "api_blue" {
  name        = "${var.project_name}-${var.environment}-api-blue"
  port        = 8000
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"

  health_check {
    enabled             = true
    path                = "/health"
    port                = "traffic-port"
    healthy_threshold   = 2
    unhealthy_threshold = 3
    timeout             = 5
    interval            = 30
    matcher             = "200"
  }

  deregistration_delay = 30

  tags = {
    Name        = "${var.project_name}-${var.environment}-api-blue-tg"
    Environment = var.environment
  }
}

resource "aws_lb_target_group" "api_green" {
  name        = "${var.project_name}-${var.environment}-api-green"
  port        = 8000
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"

  health_check {
    enabled             = true
    path                = "/health"
    port                = "traffic-port"
    healthy_threshold   = 2
    unhealthy_threshold = 3
    timeout             = 5
    interval            = 30
    matcher             = "200"
  }

  deregistration_delay = 30

  tags = {
    Name        = "${var.project_name}-${var.environment}-api-green-tg"
    Environment = var.environment
  }
}

# ============================================
# Target Groups - UI (Blue/Green)
# ============================================
resource "aws_lb_target_group" "ui_blue" {
  name        = "${var.project_name}-${var.environment}-ui-blue"
  port        = 80
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"

  health_check {
    enabled             = true
    path                = "/"
    port                = "traffic-port"
    healthy_threshold   = 2
    unhealthy_threshold = 3
    timeout             = 5
    interval            = 30
    matcher             = "200-299"
  }

  # lifecycle {
  #   create_before_destroy = true  # Create new before deleting old
  # }

  deregistration_delay = 30

  tags = {
    Name        = "${var.project_name}-${var.environment}-ui-blue-tg"
    Environment = var.environment
  }
}

resource "aws_lb_target_group" "ui_green" {
  name        = "${var.project_name}-${var.environment}-ui-green"
  port        = 80
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"

  health_check {
    enabled             = true
    path                = "/"
    port                = "traffic-port"
    healthy_threshold   = 2
    unhealthy_threshold = 3
    timeout             = 5
    interval            = 30
    matcher             = "200-299"
  }

  # lifecycle {
  #   create_before_destroy = true  # Create new before deleting old
  # }

  deregistration_delay = 30

  tags = {
    Name        = "${var.project_name}-${var.environment}-ui-green-tg"
    Environment = var.environment
  }
}

# ============================================
# Target Groups - Central (Blue/Green)
# ============================================
resource "aws_lb_target_group" "central_blue" {
  name        = "${var.project_name}-${var.environment}-central-blue"
  port        = 8100
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"

  health_check {
    enabled             = true
    path                = "/healthz"
    port                = "traffic-port"
    healthy_threshold   = 2
    unhealthy_threshold = 3
    timeout             = 5
    interval            = 30
    matcher             = "200"
  }

  deregistration_delay = 30

  tags = {
    Name        = "${var.project_name}-${var.environment}-central-blue-tg"
    Environment = var.environment
  }
}

resource "aws_lb_target_group" "central_green" {
  name        = "${var.project_name}-${var.environment}-central-green"
  port        = 8100
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"

  health_check {
    enabled             = true
    path                = "/healthz"
    port                = "traffic-port"
    healthy_threshold   = 2
    unhealthy_threshold = 3
    timeout             = 5
    interval            = 30
    matcher             = "200"
  }

  deregistration_delay = 30

  tags = {
    Name        = "${var.project_name}-${var.environment}-central-green-tg"
    Environment = var.environment
  }
}

# ============================================
# HTTP Listener (Redirect to HTTPS if certificate provided)
# ============================================
# resource "aws_lb_listener" "http" {
#   load_balancer_arn = aws_lb.main.arn
#   port              = "80"
#   protocol          = "HTTP"

#   # Default action returns 404 - all traffic goes through rules
#   default_action {
#     type = "fixed-response"
    
#     fixed_response {
#       content_type = "text/plain"
#       message_body = "Service not found"
#       status_code  = "404"
#     }
#   }
# }

# resource "aws_lb_listener" "http" {
#   load_balancer_arn = aws_lb.main.arn
#   port              = 80
#   protocol          = "HTTP"

#   # Default action for the HTTP listener: Redirect everything to HTTPS
#   default_action {
#     type = "redirect"
#     redirect {
#       port        = "443"
#       protocol    = "HTTPS"
#       status_code = "HTTP_301"
#     }
#   }
# }

resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.main.arn
  port              = 80
  protocol          = "HTTP"

  # Default action needed for Terraform compliance, CodeDeploy overwrites rules later
  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.ui_blue.arn # or a placeholder TG
  }

  lifecycle {
    ignore_changes = [default_action]  # CodeDeploy manages this
  }
}


# ============================================
# HTTPS Listener (if certificate provided)
# ============================================
resource "aws_lb_listener" "https" {
  count             = var.enable_https ? 1 : 0
  load_balancer_arn = aws_lb.main.arn
  port              = 443
  protocol          = "HTTPS"
  
  # Modern TLS policy supporting TLS 1.2 and 1.3
  ssl_policy      = "ELBSecurityPolicy-TLS13-1-2-2021-06"
  certificate_arn = var.certificate_arn

  # Default action: forward to UI (Blue target group initially)
  # CodeDeploy will manage Blue/Green switching via listener rules
  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.ui_blue.arn
  }

  # CRITICAL: CodeDeploy manages default_action during deployments
  # Do NOT remove this lifecycle block or Blue/Green deployments will fail
  lifecycle {
    ignore_changes = [default_action]
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-https-listener"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}
# resource "aws_lb_listener" "https" {
#   count             = var.enable_https ? 1 : 0
#   load_balancer_arn = aws_lb.main.arn
#   port              = "443"
#   protocol          = "HTTPS"
#   ssl_policy        = "ELBSecurityPolicy-TLS13-1-2-2021-06"
#   certificate_arn   = var.certificate_arn

#   # Default action needed for Terraform compliance, CodeDeploy overwrites rules later
#   default_action {
#     type             = "forward"
#     target_group_arn = aws_lb_target_group.ui_blue.arn # or a placeholder TG
#   }

#   lifecycle {
#     ignore_changes = [default_action]  # CodeDeploy manages this
#   }
# }

# ============================================
# Listener Rules - HTTP
# ============================================
resource "aws_lb_listener_rule" "api_http" {
  listener_arn = aws_lb_listener.http.arn
  priority     = 100

  action {
    type = "forward"
    target_group_arn = aws_lb_target_group.api_blue.arn
  }

  condition {
    path_pattern {
      values = ["/api/*"]
    }
  }

  lifecycle {
    ignore_changes = [action]
  }

  tags = {
    Name = "API HTTP Rule"
  }
}

resource "aws_lb_listener_rule" "ui_http" {
  listener_arn = aws_lb_listener.http.arn
  priority     = 200

  action {
    type = "forward"
    target_group_arn = aws_lb_target_group.ui_blue.arn
  }

  condition {
    path_pattern {
      values = ["/*"]
    }
  }

  # CRITICAL: Let CodeDeploy manage target group switching
  lifecycle {
    ignore_changes = [action]
  }

  tags = {
    Name = "UI HTTP Rule"
  }
}

resource "aws_lb_listener_rule" "central_http" {
  listener_arn = aws_lb_listener.http.arn
  priority     = 101

  action {
    type = "forward"
    target_group_arn = aws_lb_target_group.central_blue.arn
  }

  condition {
    path_pattern {
      values = ["/tracking/*"]
    }
  }

  lifecycle {
    ignore_changes = [action]
  }

  tags = {
    Name = "Central HTTP Rule"
  }
}

# ============================================
# Listener Rules - HTTPS
# ============================================
resource "aws_lb_listener_rule" "api_https" {
  count        = var.enable_https ? 1 : 0
  listener_arn = aws_lb_listener.https[0].arn
  priority     = 100

  action {
    type = "forward"
    target_group_arn = aws_lb_target_group.api_blue.arn
  }

  condition {
    path_pattern {
      values = ["/api/*"]
    }
  }

  lifecycle {
    ignore_changes = [action[0].target_group_arn]
  }

  tags = {
    Name = "API HTTPS Rule"
  }
}

resource "aws_lb_listener_rule" "ui_https" {
  count        = var.enable_https ? 1 : 0
  listener_arn = aws_lb_listener.https[0].arn
  priority     = 200

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.ui_blue.arn
  }

  condition {
    path_pattern {
      values = ["/*"]
    }
  }

  lifecycle {
    ignore_changes = [action[0].target_group_arn]
  }

  tags = {
    Name = "UI HTTPS Rule"
  }
}

resource "aws_lb_listener_rule" "central_https" {
  count        = var.enable_https ? 1 : 0
  listener_arn = aws_lb_listener.https[0].arn
  priority     = 101

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.central_blue.arn
  }

  condition {
    path_pattern {
      values = ["/tracking/*"]
    }
  }

  lifecycle {
    ignore_changes = [action[0].target_group_arn]
  }

  tags = {
    Name = "Central HTTPS Rule"
  }
}
