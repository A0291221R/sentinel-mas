output "hosted_zone_id" {
  description = "Route53 hosted zone ID"
  value       = data.aws_route53_zone.main.zone_id
}

output "domain_name" {
  description = "Full domain name"
  value       = aws_route53_record.alb.name
}

output "nameservers" {
  description = "Hosted zone nameservers"
  value       = data.aws_route53_zone.main.name_servers
}
