# Route53 & HTTPS Setup Guide

## Prerequisites

You mentioned you have **sentinel-mas.com** registered. Here's how to use it with this infrastructure.

---

## 🚀 Quick Setup (3 Steps)

### Step 1: Create Route53 Hosted Zone

If you haven't already created a hosted zone for your domain:

```bash
# Create hosted zone
aws route53 create-hosted-zone \
  --name sentinel-mas.com \
  --caller-reference $(date +%s)

# Get nameservers
aws route53 list-hosted-zones | grep sentinel-mas.com -A 10
```

**Important**: Update your domain registrar's nameservers to use AWS Route53 nameservers.

### Step 2: Enable HTTPS in Terraform

Edit `environments/dev/terraform.tfvars` or `environments/prod/terraform.tfvars`:

```hcl
# Enable HTTPS
enable_https = true
domain_name  = "sentinel-mas.com"

# For dev environment:
subdomain = "dev"  # Results in: dev.sentinel-mas.com

# For prod environment:
subdomain = ""  # Results in: sentinel-mas.com (root domain)
subject_alternative_names = ["*.sentinel-mas.com"]
create_www_redirect = true  # www.sentinel-mas.com → sentinel-mas.com
```

### Step 3: Deploy

```bash
cd environments/prod
terraform init
terraform apply
```

**Certificate validation takes 5-10 minutes**. Terraform will wait for DNS validation to complete.

---

## 📋 What Gets Created

### With `enable_https = true`:

1. **ACM Certificate**
   - Domain: `sentinel-mas.com` (or `dev.sentinel-mas.com`)
   - Wildcard: `*.sentinel-mas.com`
   - Validation: DNS (automatic via Route53)

2. **Route53 DNS Records**
   - A record pointing to ALB
   - Certificate validation records (automatic)
   - WWW redirect (if enabled)

3. **HTTPS Listener on ALB**
   - Port 443 with TLS 1.3
   - Automatic HTTP → HTTPS redirect

### With `enable_https = false`:

- HTTP only (port 80)
- No certificate
- No custom domain
- Use ALB DNS name directly

---

## 🌐 Domain Configuration Examples

### Production (Root Domain)
```hcl
# environments/prod/terraform.tfvars
enable_https              = true
domain_name               = "sentinel-mas.com"
subdomain                 = ""  # Empty for root domain
subject_alternative_names = ["*.sentinel-mas.com"]
create_www_redirect       = true
```

**Result**: 
- ✅ `https://sentinel-mas.com`
- ✅ `https://www.sentinel-mas.com` → redirects to root
- ✅ `http://sentinel-mas.com` → redirects to HTTPS

### Development (Subdomain)
```hcl
# environments/dev/terraform.tfvars
enable_https              = true
domain_name               = "sentinel-mas.com"
subdomain                 = "dev"
subject_alternative_names = []
create_www_redirect       = false
```

**Result**: 
- ✅ `https://dev.sentinel-mas.com`
- ✅ `http://dev.sentinel-mas.com` → redirects to HTTPS

### Staging Environment
```hcl
# environments/staging/terraform.tfvars
enable_https              = true
domain_name               = "sentinel-mas.com"
subdomain                 = "staging"
subject_alternative_names = []
create_www_redirect       = false
```

**Result**: `https://staging.sentinel-mas.com`

---

## 🔐 SSL/TLS Details

### Certificate Properties
- **Validation**: DNS (automatic)
- **Renewal**: Automatic by AWS
- **TLS Version**: 1.2 and 1.3
- **Security Policy**: `ELBSecurityPolicy-TLS13-1-2-2021-06`

### What's Covered
- Primary domain (e.g., `sentinel-mas.com`)
- Wildcard (e.g., `*.sentinel-mas.com`)
- All subdomains under wildcard

---

## ⏱️ Deployment Timeline

```
terraform apply
↓
[~30 sec] Create ACM certificate request
↓
[~1 min] Create Route53 validation records
↓
[5-10 min] Wait for DNS propagation & validation
↓
[~2 min] Update ALB with HTTPS listener
↓
[~5 min] Deploy ECS services
↓
✅ Done! Visit https://your-domain.com
```

**Total time**: ~15-20 minutes (first deployment)

---

## ✅ Verification Steps

### 1. Check Certificate Status
```bash
aws acm list-certificates --region us-east-1

# Check specific certificate
aws acm describe-certificate --certificate-arn YOUR_CERT_ARN
```

Should show `Status: ISSUED`

### 2. Check DNS Records
```bash
# Check A record
dig sentinel-mas.com

# Check HTTPS
curl -I https://sentinel-mas.com
```

### 3. Test Endpoints
```bash
# Should redirect to HTTPS
curl -I http://sentinel-mas.com

# Should return 200 OK
curl -I https://sentinel-mas.com/api/health
```

---

## 🛠️ Troubleshooting

### Issue: Certificate Stuck in "Pending Validation"

**Cause**: DNS propagation delay or nameserver not updated

**Solution**:
```bash
# Verify nameservers match Route53
dig NS sentinel-mas.com

# Check validation records exist
dig _acm-validation.sentinel-mas.com TXT

# If still stuck after 30 min, recreate:
terraform taint module.acm[0].aws_acm_certificate.main
terraform apply
```

### Issue: "HostedZoneNotFound"

**Cause**: Route53 hosted zone doesn't exist

**Solution**:
```bash
# Create hosted zone first
aws route53 create-hosted-zone \
  --name sentinel-mas.com \
  --caller-reference $(date +%s)

# Update your domain registrar with Route53 nameservers
```

### Issue: HTTPS Works but HTTP Doesn't Redirect

**Cause**: ALB listener rules not updated

**Solution**:
```bash
# Check ALB listeners
aws elbv2 describe-listeners --load-balancer-arn YOUR_ALB_ARN

# Should show both port 80 (redirect) and 443 (forward)
```

---

## 💰 Additional Costs

### With HTTPS Enabled:
- **Route53 Hosted Zone**: $0.50/month
- **DNS Queries**: $0.40 per million queries
- **ACM Certificate**: **FREE** ✨
- **ALB HTTPS**: Same cost as HTTP (no extra charge)

**Estimated additional cost**: ~$1-2/month (minimal)

---

## 🔄 Switching Between HTTP and HTTPS

### Enable HTTPS Later
```bash
# Edit terraform.tfvars
enable_https = true

# Apply changes
terraform apply
```

### Disable HTTPS (Revert to HTTP)
```bash
# Edit terraform.tfvars
enable_https = false

# Apply changes
terraform apply
```

---

## 🌟 Best Practices

1. **Production**: Always use `enable_https = true`
2. **Root Domain**: Use for production (`subdomain = ""`)
3. **Subdomains**: Use for dev/staging (`subdomain = "dev"`)
4. **Wildcard**: Include `*.sentinel-mas.com` for flexibility
5. **WWW Redirect**: Enable for production (`create_www_redirect = true`)

---

## 📊 Final Configuration Summary

### For Your Domain (sentinel-mas.com)

**Production**:
```hcl
enable_https = true
domain_name  = "sentinel-mas.com"
subdomain    = ""
```
→ `https://sentinel-mas.com`

**Development**:
```hcl
enable_https = true
domain_name  = "sentinel-mas.com"
subdomain    = "dev"
```
→ `https://dev.sentinel-mas.com`

---

**🎉 Your application will be accessible at your custom domain with automatic HTTPS!**
