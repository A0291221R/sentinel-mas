# ============================================
# Route53 Hosted Zone (existing)
# ============================================
data "aws_route53_zone" "main" {
  name         = var.domain_name
  private_zone = false
}

# ============================================
# ALB DNS Record
# ============================================
resource "aws_route53_record" "alb" {
  zone_id = data.aws_route53_zone.main.zone_id
  name    = var.subdomain != "" ? "${var.subdomain}.${var.domain_name}" : var.domain_name
  type    = "A"

  alias {
    name                   = var.alb_dns_name
    zone_id                = var.alb_zone_id
    evaluate_target_health = true
  }
}

# ============================================
# WWW Redirect (optional)
# ============================================
resource "aws_route53_record" "www" {
  count   = var.create_www_redirect ? 1 : 0
  zone_id = data.aws_route53_zone.main.zone_id
  name    = "www.${var.domain_name}"
  type    = "A"

  alias {
    name                   = var.alb_dns_name
    zone_id                = var.alb_zone_id
    evaluate_target_health = true
  }
}
