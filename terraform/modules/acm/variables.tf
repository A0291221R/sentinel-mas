variable "project_name" {
  description = "Project name"
  type        = string
}

variable "environment" {
  description = "Environment (dev/prod)"
  type        = string
}

variable "domain_name" {
  description = "Primary domain name"
  type        = string
}

variable "subject_alternative_names" {
  description = "Alternative domain names (e.g., *.sentinel-mas.com)"
  type        = list(string)
  default     = []
}

variable "hosted_zone_id" {
  description = "Route53 hosted zone ID"
  type        = string
}
