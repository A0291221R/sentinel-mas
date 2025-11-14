output "certificate_arn" {
  description = "ACM certificate ARN"
  value       = aws_acm_certificate.main.arn
}

output "certificate_domain_name" {
  description = "Certificate domain name"
  value       = aws_acm_certificate.main.domain_name
}

output "certificate_status" {
  description = "Certificate validation status"
  value       = aws_acm_certificate.main.status
}
