# Sentinel MAS - Deployment Guide

Step-by-step guide to deploy Sentinel MAS to AWS ECS using Terraform.

## 📋 Prerequisites Checklist

- [ ] AWS Account with administrative access
- [ ] AWS CLI installed and configured
- [ ] Terraform >= 1.0 installed
- [ ] Docker images built and pushed to ECR
- [ ] Domain name (optional, for production)

## 🔧 Pre-Deployment Setup

### 1. Create ECR Repositories

```bash
# Set your AWS region
export AWS_REGION=us-east-1

# Create ECR repositories
aws ecr create-repository --repository-name sentinel-mas-api --region $AWS_REGION
aws ecr create-repository --repository-name sentinel-mas-ui --region $AWS_REGION
aws ecr create-repository --repository-name sentinel-mas-central --region $AWS_REGION

# Get repository URLs
aws ecr describe-repositories --region $AWS_REGION | grep repositoryUri
```

### 2. Push Docker Images to ECR

```bash
# Login to ECR
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin YOUR_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# Tag and push images
docker tag sentinel-mas-api:latest YOUR_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/sentinel-mas-api:latest
docker push YOUR_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/sentinel-mas-api:latest

docker tag sentinel-mas-ui:latest YOUR_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/sentinel-mas-ui:latest
docker push YOUR_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/sentinel-mas-ui:latest

docker tag sentinel-mas-central:latest YOUR_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/sentinel-mas-central:latest
docker push YOUR_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/sentinel-mas-central:latest
```

### 3. Generate Secrets

```bash
# Generate strong database password
openssl rand -base64 32
~~
a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4

# Generate API secret key for JWT
openssl rand -base64 64 | awk '{printf "%s", $0}'

oE9c9ZXHy4yo9ttDft4HnxOxQevdHP8iVwUMiAqyDGUEAV72/AzSnGTmjGOr8Q8FhPiLAw9CvKX3+c5EnWNjtw==
~~~

# Store these securely - you'll need them for terraform.tfvars
```

## 🚀 Deployment Steps

### Step 1: Configure Terraform Variables

Navigate to your environment:

```bash
cd environments/dev  # or environments/prod
```

Edit `terraform.tfvars`:

```hcl
# Required changes
db_password    = "YOUR_GENERATED_DB_PASSWORD"
openai_api_key = "sk-YOUR_OPENAI_API_KEY"
langgraph_api_key = "YOUR_LANGGRAPH_API_KEY"
api_secret_key = "YOUR_GENERATED_API_SECRET"
allowed_list

# Update with your AWS account ID (get it with: aws sts get-caller-identity)
ecr_repository_url_api     = "123456789012.dkr.ecr.us-east-1.amazonaws.com/sentinel-mas-api"
ecr_repository_url_ui      = "123456789012.dkr.ecr.us-east-1.amazonaws.com/sentinel-mas-ui"
ecr_repository_url_central = "123456789012.dkr.ecr.us-east-1.amazonaws.com/sentinel-mas-central"

# Optional: Adjust resource configurations
api_cpu = 512     # Increase for production
api_memory = 1024 # Increase for production
```

### Step 2: Initialize Terraform

```bash
terraform init
```

Expected output:
```
Initializing modules...
Initializing the backend...
Initializing provider plugins...
Terraform has been successfully initialized!
```

### Step 3: Plan Deployment

```bash
terraform plan -out=tfplan
```

Review the plan carefully. You should see:
- ~60-80 resources to be created
- VPC, subnets, NAT gateways
- Security groups
- RDS instance
- ALB with target groups
- ECS cluster, services, task definitions
- CodeDeploy application and deployment groups

### Step 4: Apply Infrastructure

```bash
terraform apply tfplan
```

This will take approximately **15-20 minutes**. The longest operations:
- NAT Gateway creation (~3 min)
- RDS instance creation (~10 min)
- ECS services stabilization (~5 min)


alb_dns_name = "sentinel-v2-dev-alb-1931574942.us-east-1.elb.amazonaws.com"
alb_url = "http://sentinel-v2-dev-alb-1931574942.us-east-1.elb.amazonaws.com"
api_service_name = "sentinel-v2-dev-api-service"
api_url = "http://sentinel-v2-dev-alb-1931574942.us-east-1.elb.amazonaws.com/api"
central_service_name = "sentinel-v2-dev-central-service"
central_url = "http://sentinel-v2-dev-alb-1931574942.us-east-1.elb.amazonaws.com/central"
codedeploy_app_name = "sentinel-v2-dev-app"
domain_name = "Not configured"
ecs_cluster_name = "sentinel-v2-dev-cluster"
https_url = "HTTPS not enabled"
rds_endpoint = <sensitive>
ui_service_name = "sentinel-v2-dev-ui-service"
ui_url = "http://sentinel-v2-dev-alb-1931574942.us-east-1.elb.amazonaws.com"
vpc_id = "vpc-09c60867f9d124ea7"


### Tips:
# temporarily stopping ECS Cluster
aws ecs update-service \
  --cluster sentinel-v2-dev-cluster \
  --service sentinel-v2-dev-ui-service \
  --desired-count 0 \
  --region us-east-1



### Step 5: Verify Deployment

```bash
# Get the ALB DNS name
terraform output alb_dns_name

# Test API health
curl http://YOUR_ALB_DNS/api/health

# Expected response: {"status": "healthy"}

# Test UI
open http://YOUR_ALB_DNS

# Test Central
curl http://YOUR_ALB_DNS/central/healthz
```

## ✅ Post-Deployment Verification

### 1. Check ECS Services

```bash
aws ecs describe-services \
  --cluster sentinel-mas-dev-cluster \
  --services sentinel-mas-dev-api-service sentinel-mas-dev-ui-service sentinel-mas-dev-central-service

# Verify running count matches desired count
```

### 2. Check Task Health

```bash
# List running tasks
aws ecs list-tasks --cluster sentinel-mas-dev-cluster

# Describe a specific task
aws ecs describe-tasks --cluster sentinel-mas-dev-cluster --tasks TASK_ARN
```

### 3. Check Database Connectivity

```bash
# Check RDS status
aws rds describe-db-instances --db-instance-identifier sentinel-mas-dev-db

# Connect from a task (if needed)
aws ecs execute-command \
  --cluster sentinel-mas-dev-cluster \
  --task TASK_ARN \
  --container api \
  --command "psql -h RDS_ENDPOINT -U postgres -d sentinelmas" \
  --interactive
```

### 4. Monitor Logs

```bash
# API logs
aws logs tail /ecs/sentinel-mas-dev-api --follow

# UI logs
aws logs tail /ecs/sentinel-mas-dev-ui --follow

# Central logs
aws logs tail /ecs/sentinel-mas-dev-central --follow
```

## 🔄 Deploying Updates

### Method 1: Using GitHub Actions (Recommended)

Your existing CI/CD pipeline will automatically:
1. Build new Docker images
2. Push to ECR
3. Update task definitions
4. Trigger CodeDeploy Blue/Green deployment

### Method 2: Manual Deployment

```bash
# Force new deployment (pulls latest :latest tag)
aws ecs update-service \
  --cluster sentinel-mas-dev-cluster \
  --service sentinel-mas-dev-api-service \
  --force-new-deployment

# Or register new task definition with specific tag
aws ecs register-task-definition --cli-input-json file://task-def.json
```

### Method 3: Using CodeDeploy

```bash
# Create deployment with new task definition
aws deploy create-deployment \
  --application-name sentinel-mas-dev-app \
  --deployment-group-name sentinel-mas-dev-api-dg \
  --revision revisionType=String,string={content="TASK_DEFINITION_ARN"}
```

## 🔍 Monitoring & Observability

### CloudWatch Dashboards

Create a custom dashboard:

```bash
# View metrics in CloudWatch console
# Key metrics to monitor:
# - ECS Service CPU/Memory utilization
# - ALB Request count and latency
# - RDS connections and query performance
```

### Set Up Alarms

```bash
# High CPU alarm
aws cloudwatch put-metric-alarm \
  --alarm-name sentinel-mas-dev-api-high-cpu \
  --alarm-description "API service high CPU" \
  --metric-name CPUUtilization \
  --namespace AWS/ECS \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2

# Similar for Memory, HTTP 5xx errors, etc.
```

## 🔐 Security Hardening (Production)

### 1. Enable VPC Flow Logs

```hcl
# Add to your main.tf
resource "aws_flow_log" "main" {
  iam_role_arn    = aws_iam_role.flow_log.arn
  log_destination = aws_cloudwatch_log_group.flow_log.arn
  traffic_type    = "ALL"
  vpc_id          = module.networking.vpc_id
}
```

### 2. Enable WAF on ALB

```bash
# Create WAF WebACL
aws wafv2 create-web-acl --name sentinel-mas-waf --scope REGIONAL ...

# Associate with ALB
aws wafv2 associate-web-acl --web-acl-arn WAF_ARN --resource-arn ALB_ARN
```

### 3. Enable GuardDuty

```bash
aws guardduty create-detector --enable
```

### 4. Setup SSL/TLS Certificate

```bash
# Request certificate from ACM
aws acm request-certificate \
  --domain-name sentinel-mas.yourdomain.com \
  --validation-method DNS

# Update ALB listener to use HTTPS
# Add to alb module: aws_lb_listener with protocol HTTPS
```

## 📊 Scaling Configuration

### Adjust Auto Scaling

Edit `terraform.tfvars`:

```hcl
# Scale up for peak hours
api_min_capacity = 3
api_max_capacity = 20

# Schedule-based scaling (add to ECS module)
# Scale down at night: 1 task
# Scale up during day: 5 tasks
```

### Database Scaling

For production growth:

```hcl
db_instance_class = "db.t3.medium"  # or db.r6g.large for more memory
db_allocated_storage = 100
db_max_allocated_storage = 500
```

## 🗑️ Cleanup / Destruction

### Important: Backup First!

```bash
# Create RDS snapshot
aws rds create-db-snapshot \
  --db-instance-identifier sentinel-mas-dev-db \
  --db-snapshot-identifier sentinel-mas-dev-final-snapshot

# Export secrets
aws secretsmanager get-secret-value --secret-id dev/sentinel-mas/db-password > backup-secrets.json
```

### Destroy Infrastructure

```bash
cd environments/dev
terraform destroy

# Confirm by typing: yes
```

**Note**: This will delete:
- All ECS services and tasks
- RDS database (unless you skip final snapshot)
- VPC and all networking
- Load balancer
- Secrets (optionally)

## ❗ Troubleshooting

### Issue: Tasks Won't Start

**Symptom**: Service desired count > running count

**Solution**:
```bash
# Check stopped tasks
aws ecs list-tasks --cluster CLUSTER --desired-status STOPPED

# Describe stopped task for error
aws ecs describe-tasks --cluster CLUSTER --tasks TASK_ARN

# Common causes:
# - Can't pull image from ECR (check IAM permissions)
# - Can't access secrets (check task execution role)
# - Health check failing (check /health endpoint)
```

### Issue: Can't Access Application

**Symptom**: curl to ALB times out

**Solution**:
```bash
# Check target group health
aws elbv2 describe-target-health --target-group-arn TG_ARN

# Verify security groups allow traffic
aws ec2 describe-security-groups --group-ids SG_ID

# Check if tasks are in correct subnets
aws ecs describe-tasks --cluster CLUSTER --tasks TASK_ARN | grep subnet
```

### Issue: High Costs

**Solution**:
```bash
# Check NAT Gateway usage (biggest cost driver)
# Consider using VPC endpoints for AWS services
# Scale down dev environment when not in use:

terraform apply -var="api_desired_count=0" -var="ui_desired_count=0"
```

## 📚 Next Steps

1. **Stage 6**: Set up monitoring and alerting (CloudWatch, X-Ray)
2. Configure CI/CD integration for automated deployments
3. Set up custom domain with Route 53
4. Enable container insights for detailed metrics
5. Implement backup and disaster recovery procedures

---

**Deployment Complete! 🎉**

Your Sentinel MAS application is now running on AWS ECS with:
- High availability
- Auto-scaling
- Blue/Green deployments
- Comprehensive security

For support, refer to the main README.md or AWS documentation.
