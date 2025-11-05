#!/bin/bash

# Sentinel MAS - Complete Terraform Infrastructure Setup
# Master script that generates all modules, environments, and documentation

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                                                        ║${NC}"
echo -e "${BLUE}║           SENTINEL MAS - ECS INFRASTRUCTURE            ║${NC}"
echo -e "${BLUE}║          Terraform Complete Setup Generator            ║${NC}"
echo -e "${BLUE}║                                                        ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if terraform directory already exists
if [ -d "terraform" ]; then
    echo -e "${YELLOW}⚠️  Warning: 'terraform' directory already exists!${NC}"
    read -p "Do you want to overwrite it? (yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        echo -e "${RED}Setup cancelled.${NC}"
        exit 1
    fi
    rm -rf terraform
fi

# Create base directory structure
echo -e "${BLUE}📁 Creating directory structure...${NC}"
mkdir -p terraform/{modules/{networking,security-groups,iam,rds,alb,ecs,codedeploy},environments/{dev,prod}}

# Run all setup parts
echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}🚀 PART 1: Networking, Security Groups, IAM${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
bash setup-terraform-infrastructure.sh

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}🚀 PART 2: RDS and ALB${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
bash setup-terraform-part2.sh

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}🚀 PART 3: ECS and CodeDeploy${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
bash setup-terraform-part3.sh

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}🚀 PART 4: Environments (Dev & Prod)${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
bash setup-terraform-part4.sh

# Create comprehensive documentation
echo ""
echo -e "${BLUE}📚 Creating documentation...${NC}"

cat > terraform/README.md << 'EOF'
# Sentinel MAS - Terraform Infrastructure

Complete AWS ECS deployment with Blue/Green strategy using modular Terraform configuration.

## 📋 Overview

This infrastructure deploys Sentinel MAS to AWS ECS Fargate with:
- Multi-AZ VPC with public/private subnets
- PostgreSQL RDS with pgvector extension
- Application Load Balancer with health checks
- ECS services for UI, API, and Central components
- Optional Blue/Green deployment with CodeDeploy
- Auto-scaling and monitoring

## 🏗️ Architecture

```
Internet
   ↓
ALB (Public Subnets)
   ↓
ECS Fargate Tasks (Private Subnets)
   ├── UI Service (Port 80)
   ├── API Service (Port 8000)
   └── Central Service (Port 5000)
   ↓
RDS PostgreSQL (Private Subnets)
```

## 📁 Structure

```
terraform/
├── modules/              # Reusable infrastructure modules
│   ├── networking/       # VPC, subnets, NAT gateways
│   ├── security-groups/  # Security group rules
│   ├── iam/              # IAM roles and policies
│   ├── rds/              # PostgreSQL database
│   ├── alb/              # Application Load Balancer
│   ├── ecs/              # ECS cluster and services
│   └── codedeploy/       # Blue/Green deployment
└── environments/         # Environment-specific configurations
    ├── dev/              # Development environment
    └── prod/             # Production environment
```

## 🚀 Quick Start

### Prerequisites

1. **AWS CLI** configured with appropriate credentials
   ```bash
   aws configure
   ```

2. **Terraform** >= 1.0 installed
   ```bash
   terraform version
   ```

3. **Docker images** pushed to ECR
   - sentinel-mas-ui
   - sentinel-mas-api
   - sentinel-mas-central

### Deploy Development Environment

```bash
# Navigate to dev environment
cd terraform/environments/dev

# Copy and edit configuration
cp terraform.tfvars.example terraform.tfvars
nano terraform.tfvars  # Update db_password and other settings

# Initialize Terraform
terraform init

# Review planned changes
terraform plan

# Apply infrastructure
terraform apply

# Get the application URL
terraform output alb_url
```

### Deploy Production Environment

```bash
# Navigate to prod environment
cd terraform/environments/prod

# Copy and edit configuration
cp terraform.tfvars.example terraform.tfvars
nano terraform.tfvars  # Update all production settings

# Initialize with S3 backend (first time)
terraform init

# Review planned changes
terraform plan

# Apply infrastructure
terraform apply

# Get outputs
terraform output
```

## ⚙️ Configuration

### Required Variables

Edit `terraform.tfvars` in each environment:

```hcl
# Database password (required)
db_password = "YourSecurePassword123!"

# Optional: Container image tag
image_tag = "latest"  # or "v1.0.0" for prod

# Optional: HTTPS certificate
certificate_arn = "arn:aws:acm:us-east-1:123456789012:certificate/xxxxx"
```

### Environment Differences

| Setting | Development | Production |
|---------|-------------|------------|
| NAT Gateways | 1 (optional) | 2 |
| RDS Multi-AZ | No | Yes |
| Instance Class | db.t3.micro | db.t3.small+ |
| Auto-scaling | Disabled | Enabled |
| CodeDeploy | Disabled | Enabled |
| Alarms | Disabled | Enabled |
| Backup Retention | 3 days | 30 days |

## 📊 Cost Optimization

### Development (~$50-80/month)
- Use single NAT Gateway or disable it
- Use db.t3.micro instance
- Disable Multi-AZ
- Disable auto-scaling
- Disable Container Insights
- Set desired_count = 1

### Production (~$200-400/month)
- Depends on traffic and scaling
- Use reserved capacity for predictable workloads
- Enable auto-scaling to optimize costs
- Regular cost reviews with AWS Cost Explorer

## 🔄 Deployment Workflow

### Initial Deployment

```bash
# 1. Initialize
terraform init

# 2. Plan (review changes)
terraform plan -out=tfplan

# 3. Apply
terraform apply tfplan

# 4. Verify
aws ecs list-services --cluster sentinel-mas-dev-cluster
```

### Update Application

```bash
# Option 1: Update via Terraform (changes task definition)
terraform apply -var="image_tag=v1.1.0"

# Option 2: Force new deployment (same image)
aws ecs update-service \
  --cluster sentinel-mas-dev-cluster \
  --service sentinel-mas-dev-api \
  --force-new-deployment

# Option 3: Blue/Green with CodeDeploy (prod only)
aws deploy create-deployment \
  --application-name sentinel-mas-prod \
  --deployment-group-name sentinel-mas-prod-api \
  --deployment-config-name CodeDeployDefault.ECSCanary10Percent5Minutes
```

### Rollback

```bash
# Terraform rollback (revert to previous state)
terraform apply -var="image_tag=v1.0.0"

# Or use CodeDeploy stop & rollback
aws deploy stop-deployment \
  --deployment-id d-XXXXX \
  --auto-rollback-enabled
```

## 🔒 Security Best Practices

- ✅ All services run in private subnets
- ✅ Database not publicly accessible
- ✅ Security groups with least privilege
- ✅ IAM roles with minimum permissions
- ✅ Encrypted RDS storage
- ✅ Non-root container users
- ✅ Secrets via AWS Secrets Manager/SSM
- ✅ HTTPS for production (recommended)

## 🐛 Troubleshooting

### Common Issues

**ECS tasks not starting:**
```bash
# Check service events
aws ecs describe-services \
  --cluster sentinel-mas-dev-cluster \
  --services sentinel-mas-dev-api

# Check CloudWatch logs
aws logs tail /ecs/sentinel-mas-dev-api --follow
```

**Database connection failed:**
```bash
# Verify security group rules
aws ec2 describe-security-groups \
  --group-ids sg-xxxxx

# Test from ECS task
aws ecs execute-command \
  --cluster sentinel-mas-dev-cluster \
  --task task-id \
  --command "/bin/sh" \
  --interactive
```

**ALB health checks failing:**
```bash
# Check target health
aws elbv2 describe-target-health \
  --target-group-arn arn:aws:elasticloadbalancing:...

# Update health check settings
terraform apply -var="api_health_check_path=/api/health"
```

### State Issues

```bash
# Refresh state
terraform refresh

# Force unlock (if locked)
terraform force-unlock LOCK_ID

# Import existing resource
terraform import module.rds.aws_db_instance.main sentinel-mas-dev-db
```

## 📈 Monitoring

### CloudWatch Dashboards

1. Navigate to CloudWatch Console
2. View pre-configured metrics:
   - ECS CPU/Memory utilization
   - ALB request count & latency
   - RDS connections & performance
   - Target health status

### Alarms (Production)

Configured alarms:
- High CPU/Memory on ECS tasks
- Unhealthy target count
- RDS storage low
- Database CPU high

### Logs

```bash
# View logs for specific service
aws logs tail /ecs/sentinel-mas-prod-api --follow

# Search logs
aws logs filter-log-events \
  --log-group-name /ecs/sentinel-mas-prod-api \
  --filter-pattern "ERROR"

# Export logs to S3
aws logs create-export-task \
  --log-group-name /ecs/sentinel-mas-prod-api \
  --from 1640000000000 \
  --to 1640100000000 \
  --destination s3-bucket-name
```

## 🔧 Maintenance

### Database Maintenance

```bash
# Create manual snapshot
aws rds create-db-snapshot \
  --db-instance-identifier sentinel-mas-prod-db \
  --db-snapshot-identifier manual-backup-$(date +%Y%m%d)

# Restore from snapshot
# (Update terraform.tfvars with snapshot_identifier)
terraform apply
```

### Scaling

```bash
# Manual scale
aws ecs update-service \
  --cluster sentinel-mas-prod-cluster \
  --service sentinel-mas-prod-api \
  --desired-count 5

# Or update in terraform.tfvars
api_desired_count = 5
terraform apply
```

## 📚 Additional Resources

- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [ECS Best Practices](https://docs.aws.amazon.com/AmazonECS/latest/bestpracticesguide/)
- [CodeDeploy Blue/Green](https://docs.aws.amazon.com/codedeploy/latest/userguide/deployment-groups-create-blue-green.html)
- [RDS PostgreSQL](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_PostgreSQL.html)

## 🆘 Support

For issues or questions:
1. Check CloudWatch logs
2. Review Terraform state
3. Verify security group rules
4. Check IAM permissions
5. Review AWS service limits

## 📝 License

This infrastructure code is part of Sentinel MAS project.
EOF

# Create deployment guide
cat > terraform/DEPLOYMENT_GUIDE.md << 'EOF'
# Sentinel MAS - Deployment Guide

Step-by-step guide for deploying Sentinel MAS to AWS.

## 📋 Pre-Deployment Checklist

- [ ] AWS account with appropriate permissions
- [ ] AWS CLI installed and configured
- [ ] Terraform >= 1.0 installed
- [ ] Docker images built and tested locally
- [ ] ECR repositories created
- [ ] Domain name (for production)
- [ ] SSL certificate (for production)

## 🎯 Step 1: Prepare Docker Images

### Build Images

```bash
# Navigate to project root
cd sentinel-mas

# Build UI
docker build -t sentinel-mas-ui:latest -f ui/Dockerfile ui/

# Build API
docker build -t sentinel-mas-api:latest -f api/Dockerfile api/

# Build Central
docker build -t sentinel-mas-central:latest -f central/Dockerfile central/
```

### Create ECR Repositories

```bash
# Set AWS region
export AWS_REGION=us-east-1
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Create repositories
aws ecr create-repository --repository-name sentinel-mas-ui --region $AWS_REGION
aws ecr create-repository --repository-name sentinel-mas-api --region $AWS_REGION
aws ecr create-repository --repository-name sentinel-mas-central --region $AWS_REGION
```

### Push Images to ECR

```bash
# Login to ECR
aws ecr get-login-password --region $AWS_REGION | \
  docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# Tag images
docker tag sentinel-mas-ui:latest $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/sentinel-mas-ui:latest
docker tag sentinel-mas-api:latest $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/sentinel-mas-api:latest
docker tag sentinel-mas-central:latest $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/sentinel-mas-central:latest

# Push images
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/sentinel-mas-ui:latest
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/sentinel-mas-api:latest
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/sentinel-mas-central:latest
```

## 🎯 Step 2: Configure Terraform

### Development Environment

```bash
cd terraform/environments/dev

# Copy example configuration
cp terraform.tfvars.example terraform.tfvars

# Edit configuration
nano terraform.tfvars
```

**Minimum required changes:**
```hcl
db_password = "YourSecurePassword123!"
```

**Optional optimizations for cost:**
```hcl
enable_nat_gateway = false  # Saves ~$32/month
db_instance_class  = "db.t3.micro"
```

### Production Environment

```bash
cd terraform/environments/prod

# Copy example configuration
cp terraform.tfvars.example terraform.tfvars

# Edit configuration
nano terraform.tfvars
```

**Required changes:**
```hcl
db_password = "ProductionSecurePassword123!"
certificate_arn = "arn:aws:acm:us-east-1:123456789012:certificate/xxxxx"
domain_name = "sentinel.yourdomain.com"
```

## 🎯 Step 3: Deploy Infrastructure

### Development Deployment

```bash
cd terraform/environments/dev

# Initialize Terraform
terraform init

# Validate configuration
terraform validate

# Format code
terraform fmt -recursive

# Review plan
terraform plan

# Apply (you'll be prompted to confirm)
terraform apply

# Or apply without prompt
terraform apply -auto-approve
```

**Expected time:** 10-15 minutes

**Watch the deployment:**
```bash
# In another terminal
watch -n 5 'aws ecs describe-services \
  --cluster sentinel-mas-dev-cluster \
  --services sentinel-mas-dev-api \
  --query services[0].events[0:3] \
  --output table'
```

### Production Deployment

```bash
cd terraform/environments/prod

# Initialize with S3 backend
terraform init

# Review plan
terraform plan -out=prod.tfplan

# Apply with saved plan
terraform apply prod.tfplan
```

**Expected time:** 15-20 minutes

## 🎯 Step 4: Post-Deployment Verification

### Get Application URL

```bash
# Get ALB DNS name
terraform output alb_url

# Example output:
# http://sentinel-mas-dev-alb-1234567890.us-east-1.elb.amazonaws.com
```

### Verify Services

```bash
# Check ECS services
aws ecs list-services --cluster sentinel-mas-dev-cluster

# Check task status
aws ecs list-tasks --cluster sentinel-mas-dev-cluster

# Describe tasks for details
aws ecs describe-tasks \
  --cluster sentinel-mas-dev-cluster \
  --tasks $(aws ecs list-tasks --cluster sentinel-mas-dev-cluster --query 'taskArns[0]' --output text)
```

### Test Health Endpoints

```bash
# Get ALB URL
ALB_URL=$(terraform output -raw alb_url)

# Test UI
curl $ALB_URL

# Test API health
curl $ALB_URL/api/health

# Expected response: {"status": "healthy"}
```

### Check Logs

```bash
# View UI logs
aws logs tail /ecs/sentinel-mas-dev-ui --follow

# View API logs
aws logs tail /ecs/sentinel-mas-dev-api --follow

# View Central logs
aws logs tail /ecs/sentinel-mas-dev-central --follow
```

## 🎯 Step 5: Configure DNS (Production Only)

### Route53 Configuration

```bash
# Get ALB details
ALB_DNS=$(terraform output -raw alb_dns_name)
ALB_ZONE_ID=$(terraform output -raw alb_zone_id)

# Create Route53 record
aws route53 change-resource-record-sets \
  --hosted-zone-id Z1234567890ABC \
  --change-batch '{
    "Changes": [{
      "Action": "CREATE",
      "ResourceRecordSet": {
        "Name": "sentinel.yourdomain.com",
        "Type": "A",
        "AliasTarget": {
          "HostedZoneId": "'$ALB_ZONE_ID'",
          "DNSName": "'$ALB_DNS'",
          "EvaluateTargetHealth": true
        }
      }
    }]
  }'
```

## 🎯 Step 6: Initialize Database

```bash
# Get database endpoint
DB_ENDPOINT=$(terraform output -raw db_address)

# Connect via bastion or ECS task
aws ecs execute-command \
  --cluster sentinel-mas-dev-cluster \
  --task <task-id> \
  --command "/bin/bash" \
  --interactive

# Inside container
psql -h $DB_ENDPOINT -U postgres -d sentinel

# Run migrations
python manage.py migrate
```

## 🔄 Updating the Application

### Update with New Image

```bash
# Build and push new image
docker build -t sentinel-mas-api:v1.1.0 -f api/Dockerfile api/
docker tag sentinel-mas-api:v1.1.0 $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/sentinel-mas-api:v1.1.0
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/sentinel-mas-api:v1.1.0

# Update terraform
cd terraform/environments/dev
terraform apply -var="image_tag=v1.1.0"
```

### Force New Deployment

```bash
# Without changing image
aws ecs update-service \
  --cluster sentinel-mas-dev-cluster \
  --service sentinel-mas-dev-api \
  --force-new-deployment
```

## 🐛 Troubleshooting

### Tasks Not Starting

```bash
# Check stopped tasks
aws ecs list-tasks \
  --cluster sentinel-mas-dev-cluster \
  --desired-status STOPPED

# Get stopped task details
aws ecs describe-tasks \
  --cluster sentinel-mas-dev-cluster \
  --tasks <task-arn>

# Common issues:
# 1. Image not found -> Check ECR repository
# 2. Resource limits -> Check CPU/memory allocation
# 3. Health check failing -> Verify health endpoint
```

### Database Connection Issues

```bash
# Verify security group
aws ec2 describe-security-groups \
  --group-ids <rds-sg-id> \
  --query 'SecurityGroups[0].IpPermissions'

# Check database status
aws rds describe-db-instances \
  --db-instance-identifier sentinel-mas-dev-db \
  --query 'DBInstances[0].DBInstanceStatus'
```

### ALB Health Check Failures

```bash
# Check target health
aws elbv2 describe-target-health \
  --target-group-arn <target-group-arn>

# Check health check configuration
aws elbv2 describe-target-groups \
  --target-group-arns <target-group-arn> \
  --query 'TargetGroups[0].HealthCheckPath'
```

## 💰 Cost Breakdown

### Development (~$50-80/month)
- NAT Gateway: $32/month (optional)
- RDS db.t3.micro: $15/month
- ECS Fargate: $20-30/month
- ALB: $16/month
- Data transfer: varies

### Production (~$200-400/month)
- NAT Gateways (2): $64/month
- RDS db.t3.small Multi-AZ: $60/month
- ECS Fargate (scaled): $100-200/month
- ALB: $16/month
- Data transfer: varies
- Backups & logs: $10-20/month

## 📊 Monitoring Setup

### Enable Container Insights

```hcl
# In terraform.tfvars
enable_container_insights = true
```

### CloudWatch Dashboard

```bash
# Create custom dashboard
aws cloudwatch put-dashboard \
  --dashboard-name sentinel-mas-dev \
  --dashboard-body file://dashboard.json
```

## 🆘 Getting Help

If you encounter issues:

1. Check CloudWatch Logs
2. Review ECS service events
3. Verify security group rules
4. Check IAM permissions
5. Review Terraform state

## ✅ Success Checklist

- [ ] All ECS tasks running
- [ ] ALB health checks passing
- [ ] Application accessible via URL
- [ ] Database migrations completed
- [ ] Logs visible in CloudWatch
- [ ] DNS configured (production)
- [ ] HTTPS working (production)
- [ ] Monitoring dashboards set up

Congratulations! Your Sentinel MAS deployment is complete! 🎉
EOF

# Create .gitignore
cat > terraform/.gitignore << 'EOF'
# Local .terraform directories
**/.terraform/*

# .tfstate files
*.tfstate
*.tfstate.*

# Crash log files
crash.log
crash.*.log

# Exclude all .tfvars files (they contain secrets)
*.tfvars
*.tfvars.json

# Exclude override files
override.tf
override.tf.json
*_override.tf
*_override.tf.json

# Exclude CLI configuration files
.terraformrc
terraform.rc

# Lock files (commit these in team environments)
# .terraform.lock.hcl
EOF

# Final summary
echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                                                        ║${NC}"
echo -e "${GREEN}║              ✅ SETUP COMPLETE!                         ║${NC}"
echo -e "${GREEN}║                                                        ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}📁 Created Structure:${NC}"
echo ""
echo "terraform/"
echo "├── modules/"
echo "│   ├── networking/       ✅ VPC, Subnets, NAT"
echo "│   ├── security-groups/  ✅ Security Rules"
echo "│   ├── iam/              ✅ Roles & Policies"
echo "│   ├── rds/              ✅ PostgreSQL + pgvector"
echo "│   ├── alb/              ✅ Load Balancer"
echo "│   ├── ecs/              ✅ Fargate Services"
echo "│   └── codedeploy/       ✅ Blue/Green Deployment"
echo "├── environments/"
echo "│   ├── dev/              ✅ Development Config"
echo "│   └── prod/             ✅ Production Config"
echo "├── README.md             ✅ Main Documentation"
echo "├── DEPLOYMENT_GUIDE.md   ✅ Step-by-Step Guide"
echo "└── .gitignore            ✅ Git Configuration"
echo ""
echo -e "${YELLOW}📋 Next Steps:${NC}"
echo ""
echo "1️⃣  Build and push Docker images to ECR"
echo "   cd /path/to/sentinel-mas"
echo "   # Follow Step 1 in DEPLOYMENT_GUIDE.md"
echo ""
echo "2️⃣  Configure Development environment"
echo "   cd terraform/environments/dev"
echo "   cp terraform.tfvars.example terraform.tfvars"
echo "   nano terraform.tfvars  # Edit db_password"
echo ""
echo "3️⃣  Deploy infrastructure"
echo "   terraform init"
echo "   terraform plan"
echo "   terraform apply"
echo ""
echo "4️⃣  Get application URL"
echo "   terraform output alb_url"
echo ""
echo -e "${GREEN}📚 Documentation:${NC}"
echo "   • terraform/README.md - Complete reference"
echo "   • terraform/DEPLOYMENT_GUIDE.md - Step-by-step deployment"
echo ""
echo -e "${BLUE}🎯 Features Included:${NC}"
echo "   ✅ Multi-AZ VPC with public/private subnets"
echo "   ✅ PostgreSQL RDS with pgvector extension"
echo "   ✅ Application Load Balancer"
echo "   ✅ ECS Fargate for all services"
echo "   ✅ Auto-scaling policies"
echo "   ✅ Blue/Green deployment with CodeDeploy"
echo "   ✅ CloudWatch monitoring and alarms"
echo "   ✅ Security groups with least privilege"
echo "   ✅ IAM roles with minimum permissions"
echo ""
echo -e "${GREEN}🚀 Ready to deploy! Follow the DEPLOYMENT_GUIDE.md${NC}"
echo ""
