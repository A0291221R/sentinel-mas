variable "domain_name" {
  description = "Domain name (e.g., sentinel-mas.com)"
  type        = string
}

variable "subdomain" {
  description = "Subdomain (e.g., 'dev' for dev.sentinel-mas.com, empty for root domain)"
  type        = string
  default     = ""
}

variable "alb_dns_name" {
  description = "ALB DNS name"
  type        = string
}

variable "alb_zone_id" {
  description = "ALB zone ID"
  type        = string
}

variable "create_www_redirect" {
  description = "Create www subdomain redirect"
  type        = bool
  default     = false
}
