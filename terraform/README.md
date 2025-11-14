# Sentinel MAS - ECS Terraform Infrastructure

Complete Terraform infrastructure for deploying Sentinel MAS to AWS ECS with Blue/Green deployment strategy.

## 📦 What's Included

### Terraform Modules
- **networking** - VPC, subnets, NAT gateways, route tables
- **security-groups** - Security groups for ALB, ECS services, and RDS
- **iam** - IAM roles for ECS tasks and CodeDeploy
- **rds** - PostgreSQL database with Multi-AZ support
- **alb** - Application Load Balancer with Blue/Green target groups
- **ecs** - ECS Fargate cluster, task definitions, services, and auto-scaling
- **codedeploy** - Blue/Green deployment with 10% canary strategy

### Environments
- **dev** - Development environment (cost-optimized)
- **prod** - Production environment (high availability, Multi-AZ)

### 🆕 Optional: Custom Domain & HTTPS
- **route53** - DNS management with automatic records
- **acm** - Free SSL/TLS certificates with auto-renewal
- **HTTPS Support** - Automatic HTTP → HTTPS redirect

---

## ✨ Features

### Core Infrastructure
- ✅ VPC with public/private subnets across multiple AZs
- ✅ Application Load Balancer with health checks
- ✅ ECS Fargate with 3 services (API, UI, Central)
- ✅ RDS PostgreSQL with Multi-AZ support
- ✅ Auto-scaling based on CPU utilization
- ✅ Blue/Green deployments via CodeDeploy

### Security & Compliance
- ✅ Secrets Manager for sensitive data
- ✅ Security groups with least-privilege access
- ✅ IAM roles with minimal permissions
- ✅ Encrypted RDS storage
- ✅ CloudWatch logging (30-day retention)

### 🆕 Custom Domain & HTTPS (Optional)
- ✅ Route53 DNS management
- ✅ ACM SSL/TLS certificates (FREE)
- ✅ Automatic certificate renewal
- ✅ HTTP → HTTPS redirect
- ✅ Support for root domain and subdomains
- ✅ Wildcard certificates for flexibility

## 🚀 Quick Start

### Prerequisites
1. AWS CLI configured with appropriate credentials
2. Terraform >= 1.0 installed
3. Docker images pushed to ECR:
   - `sentinel-mas-api:latest`
   - `sentinel-mas-ui:latest`
   - `sentinel-mas-central:latest`

### Step 1: Configure Variables

Edit `environments/dev/terraform.tfvars` or `environments/prod/terraform.tfvars`:

```hcl
# Update these values
db_password    = "your-strong-password"
openai_api_key = "sk-your-openai-key"
langgraph_api_key = "your-langgraph-api-key"
api_secret_key = "your-jwt-secret"
sentinel_db_url= ""

# Update ECR URLs with your AWS account ID
ecr_repository_url_api = "YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/sentinel-mas-api"
```

### Step 2: Deploy Dev Environment

```bash
cd environments/dev

# Initialize Terraform
terraform init

# Preview changes
terraform plan

# Deploy infrastructure
terraform apply

# Get application URL
terraform output alb_dns_name
```

### Step 3: Access Your Application

```bash
# API endpoint
curl http://YOUR_ALB_DNS/api/health

# UI endpoint
open http://YOUR_ALB_DNS

# Central endpoint
curl http://YOUR_ALB_DNS/central/health
```

### 🆕 Step 4: (Optional) Enable Custom Domain & HTTPS

If you have a registered domain (e.g., `sentinel-mas.com`):

```bash
# Edit terraform.tfvars
enable_https = true
domain_name  = "sentinel-mas.com"
subdomain    = "dev"  # Results in: dev.sentinel-mas.com

# Apply changes
terraform apply
```

**See [ROUTE53-SETUP.md](ROUTE53-SETUP.md) for detailed instructions.**

**Result**: Access your app at `https://dev.sentinel-mas.com` with automatic SSL!

## 📊 Architecture

```
Internet
    ↓
Application Load Balancer (Public Subnets)
    ↓
    ├─→ API Service (Private Subnets)
    ├─→ UI Service (Private Subnets)
    └─→ Central Service (Private Subnets)
            ↓
    RDS PostgreSQL (Private Subnets, Multi-AZ)
```

## 🔄 Blue/Green Deployment

The infrastructure uses AWS CodeDeploy for zero-downtime deployments:

1. **Canary Strategy**: 10% traffic to new version for 5 minutes
2. **Monitoring**: CloudWatch alarms monitored during canary
3. **Auto Rollback**: Automatic rollback on failures
4. **Full Deployment**: 100% traffic shift after successful canary

### Trigger Deployment

```bash
# From your CI/CD pipeline or manually:
aws deploy create-deployment \
  --application-name sentinel-mas-dev-app \
  --deployment-group-name sentinel-mas-dev-api-dg \
  --revision '{"revisionType":"String","string":{"content":"TASK_DEFINITION_ARN"}}'
```

## 💰 Cost Estimates

### Dev Environment
- VPC & Networking: ~$50/month (NAT Gateway)
- RDS (db.t3.micro): ~$15/month
- ECS Fargate: ~$40-65/month (3 services, 1 task each)
- ALB: ~$25/month
- **Total: ~$130-155/month**

### Prod Environment
- VPC & Networking: ~$150/month (3 NAT Gateways)
- RDS (db.t3.small, Multi-AZ): ~$60/month
- ECS Fargate: ~$150-250/month (3 services, 2+ tasks each)
- ALB: ~$25/month
- **Total: ~$385-485/month**

## 🔐 Security Features

- Private subnets for all compute resources
- Secrets stored in AWS Secrets Manager
- Security groups with least-privilege access
- Encrypted RDS storage
- IAM roles with minimal permissions
- VPC Flow Logs (optional)

## 📈 Auto Scaling

All services auto-scale based on CPU utilization:
- **Target**: 70% CPU
- **Scale Out**: When CPU > 70% for 2 minutes
- **Scale In**: When CPU < 70% for 15 minutes

### Dev Limits
- Min: 1 task | Max: 3 tasks per service

### Prod Limits
- Min: 2 tasks | Max: 10 tasks per service

## 🔧 Maintenance Commands

### View ECS Services
```bash
aws ecs list-services --cluster sentinel-mas-dev-cluster
```

### View Running Tasks
```bash
aws ecs list-tasks --cluster sentinel-mas-dev-cluster --service-name sentinel-mas-dev-api-service
```

### View Logs
```bash
aws logs tail /ecs/sentinel-mas-dev-api --follow
```

### Update Task Definition
```bash
aws ecs update-service \
  --cluster sentinel-mas-dev-cluster \
  --service sentinel-mas-dev-api-service \
  --force-new-deployment
```

## 🗑️ Cleanup

```bash
cd environments/dev
terraform destroy
```

**Warning**: This will delete all resources including the database. Ensure you have backups!

## 📝 Module Documentation

Each module has its own README with detailed documentation:
- See `modules/*/README.md` for module-specific details

## 🆘 Troubleshooting

### Service Won't Start
Check task execution role permissions and ECR image accessibility:
```bash
aws ecs describe-tasks --cluster CLUSTER --tasks TASK_ARN
```

### Can't Access Database
Verify security group rules and RDS endpoint:
```bash
aws rds describe-db-instances --db-instance-identifier sentinel-mas-dev-db
```

### Deployment Fails
Check CodeDeploy deployment status:
```bash
aws deploy list-deployments --application-name sentinel-mas-dev-app
```

## 📚 Additional Resources

- [AWS ECS Best Practices](https://docs.aws.amazon.com/AmazonECS/latest/bestpracticesguide/)
- [Terraform AWS Provider Docs](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [CodeDeploy Blue/Green Guide](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/deployment-type-bluegreen.html)

## 🤝 Support

For issues or questions:
1. Check the troubleshooting section
2. Review CloudWatch logs
3. Check AWS service health dashboard

---

**Built with ❤️ using Terraform and AWS ECS**
