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

  lifecycle {
    create_before_destroy = true  # Create new before deleting old
  }

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

  lifecycle {
    create_before_destroy = true  # Create new before deleting old
  }

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
resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.main.arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type = var.certificate_arn != "" ? "redirect" : "forward"
    
    # Only set target_group_arn when forwarding (no certificate)
    target_group_arn = var.certificate_arn == "" ? aws_lb_target_group.ui_blue.arn : null

    # Redirect config (only when certificate exists)
    dynamic "redirect" {
      for_each = var.certificate_arn != "" ? [1] : []
      content {
        port        = "443"
        protocol    = "HTTPS"
        status_code = "HTTP_301"
      }
    }
  }
}
# resource "aws_lb_listener" "http" {
#   load_balancer_arn = aws_lb.main.arn
#   port              = "80"
#   protocol          = "HTTP"

#   default_action {
#     type = var.certificate_arn != "" ? "redirect" : "fixed-response"

#     dynamic "redirect" {
#       for_each = var.certificate_arn != "" ? [1] : []
#       content {
#         port        = "443"
#         protocol    = "HTTPS"
#         status_code = "HTTP_301"
#       }
#     }

#     dynamic "fixed_response" {
#       for_each = var.certificate_arn == "" ? [1] : []
#       content {
#         content_type = "text/plain"
#         message_body = "Service not found"
#         status_code  = "404"
#       }
#     }
#   }
# }

# ============================================
# HTTPS Listener (if certificate provided)
# ============================================
resource "aws_lb_listener" "https" {
  count             = var.certificate_arn != "" ? 1 : 0
  load_balancer_arn = aws_lb.main.arn
  port              = "443"
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS13-1-2-2021-06"
  certificate_arn   = var.certificate_arn

  default_action {
    type = "fixed-response"
    fixed_response {
      content_type = "text/plain"
      message_body = "Service not found"
      status_code  = "404"
    }
  }
}

# ============================================
# Listener Rules - HTTP
# ============================================
resource "aws_lb_listener_rule" "api_http" {
  listener_arn = aws_lb_listener.http.arn
  priority     = 100

  action {
    type             = var.certificate_arn != "" ? "redirect" : "forward"
    
    dynamic "redirect" {
      for_each = var.certificate_arn != "" ? [1] : []
      content {
        port        = "443"
        protocol    = "HTTPS"
        status_code = "HTTP_301"
      }
    }

    target_group_arn = var.certificate_arn == "" ? aws_lb_target_group.api_blue.arn : null
  }

  condition {
    path_pattern {
      values = ["/api/*"]
    }
  }
}

# resource "aws_lb_listener_rule" "ui_http" {
#   listener_arn = aws_lb_listener.http.arn
#   priority     = 200

#   action {
#     type             = var.certificate_arn != "" ? "redirect" : "forward"
    
#     dynamic "redirect" {
#       for_each = var.certificate_arn != "" ? [1] : []
#       content {
#         port        = "443"
#         protocol    = "HTTPS"
#         status_code = "HTTP_301"
#       }
#     }

#     target_group_arn = var.certificate_arn == "" ? aws_lb_target_group.ui_blue.arn : null
#   }

#   condition {
#     path_pattern {
#       values = ["/"]
#     }
#   }
# }

resource "aws_lb_listener_rule" "central_http" {
  listener_arn = aws_lb_listener.http.arn
  priority     = 101

  action {
    type             = var.certificate_arn != "" ? "redirect" : "forward"
    
    dynamic "redirect" {
      for_each = var.certificate_arn != "" ? [1] : []
      content {
        port        = "443"
        protocol    = "HTTPS"
        status_code = "HTTP_301"
      }
    }

    target_group_arn = var.certificate_arn == "" ? aws_lb_target_group.central_blue.arn : null
  }

  condition {
    path_pattern {
      values = ["/tracking/*"]
    }
  }
}

# ============================================
# Listener Rules - HTTPS
# ============================================
resource "aws_lb_listener_rule" "api_https" {
  count        = var.certificate_arn != "" ? 1 : 0
  listener_arn = aws_lb_listener.https[0].arn
  priority     = 100

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.api_blue.arn
  }

  condition {
    path_pattern {
      values = ["/api/*"]
    }
  }
}

resource "aws_lb_listener_rule" "ui_https" {
  count        = var.certificate_arn != "" ? 1 : 0
  listener_arn = aws_lb_listener.https[0].arn
  priority     = 200

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.ui_blue.arn
  }

  condition {
    path_pattern {
      values = ["/"]
    }
  }
}

resource "aws_lb_listener_rule" "central_https" {
  count        = var.certificate_arn != "" ? 1 : 0
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
}
