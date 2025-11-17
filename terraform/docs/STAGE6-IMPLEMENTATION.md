# Stage 6 Implementation Guide

## Prerequisites
- ✅ Stage 5 completed (ECS services running)
- ✅ Terraform 1.0+ installed
- ✅ AWS CLI configured

## Directory Structure

```
terraform/
├── modules/
│   ├── monitoring/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   └── xray/
│       ├── main.tf
│       └── variables_outputs.tf
└── environments/
    └── dev/
        └── monitoring.tf
```

## Step 1: Add Monitoring Module to Your Environment

Create `terraform/environments/dev/monitoring.tf`:

```hcl
module "monitoring" {
  source = "../../modules/monitoring"

  environment    = "dev"
  aws_region     = "ap-southeast-1"
  cluster_name   = module.ecs.cluster_name
  alb_arn_suffix = module.alb.alb_arn_suffix
  db_instance_id = module.rds.db_instance_id

  log_retention_days = 7  # 7 days for dev, 30 for prod

  alert_emails = [
    "team@example.com",
    "ops@example.com"
  ]

  cpu_alarm_threshold    = 80
  memory_alarm_threshold = 80
}

module "xray" {
  source = "../../modules/xray"

  environment = "dev"

  api_task_role_name     = module.ecs.api_task_role_name
  ui_task_role_name      = module.ecs.ui_task_role_name
  central_task_role_name = module.ecs.central_task_role_name
}

# Outputs
output "dashboard_url" {
  value = "https://console.aws.amazon.com/cloudwatch/home?region=ap-southeast-1#dashboards:name=${module.monitoring.dashboard_name}"
}

output "xray_console_url" {
  value = "https://console.aws.amazon.com/xray/home?region=ap-southeast-1#/service-map"
}
```

## Step 2: Update ECS Task Definitions

Add X-Ray sidecar to your task definitions. Update `modules/ecs/main.tf`:

```hcl
# API Task Definition with X-Ray
resource "aws_ecs_task_definition" "api" {
  family                   = "${var.environment}-sentinel-mas-api"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = 512
  memory                   = 1024
  execution_role_arn       = aws_iam_role.execution.arn
  task_role_arn            = aws_iam_role.api_task.arn

  container_definitions = jsonencode([
    {
      name      = "api"
      image     = "${var.ecr_api_url}:latest"
      cpu       = 480
      memory    = 768
      essential = true

      environment = [
        {
          name  = "AWS_XRAY_DAEMON_ADDRESS"
          value = "xray-daemon:2000"
        },
        {
          name  = "AWS_XRAY_TRACING_NAME"
          value = "${var.environment}-sentinel-mas-api"
        },
        {
          name  = "NODE_ENV"
          value = var.environment
        }
      ]

      portMappings = [
        {
          containerPort = 3000
          protocol      = "tcp"
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = var.api_log_group_name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "api"
        }
      }
    },
    {
      name      = "xray-daemon"
      image     = "public.ecr.aws/xray/aws-xray-daemon:latest"
      cpu       = 32
      memory    = 256
      essential = true

      portMappings = [
        {
          containerPort = 2000
          protocol      = "udp"
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = "/ecs/${var.environment}/xray-daemon"
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "xray"
        }
      }
    }
  ])
}
```

Repeat for UI and Central services.

## Step 3: Deploy Terraform

```bash
cd terraform/environments/dev

# Initialize new modules
terraform init

# Preview changes
terraform plan

# Deploy monitoring stack
terraform apply

# Confirm email subscriptions (check your inbox)
```

## Step 4: Update Application Code

### For Node.js Services (API & Central)

1. Install X-Ray SDK:
```bash
npm install aws-xray-sdk-core aws-xray-sdk-express
```

2. Update `package.json`:
```json
{
  "dependencies": {
    "aws-xray-sdk-core": "^3.5.0",
    "aws-xray-sdk-express": "^3.5.0"
  }
}
```

3. Instrument your app (see `docs/xray-instrumentation-nodejs.md`)

4. Rebuild and push Docker images:
```bash
docker build -t sentinel-mas-api .
docker tag sentinel-mas-api:latest YOUR_ECR_URL/sentinel-mas-api:latest
docker push YOUR_ECR_URL/sentinel-mas-api:latest
```

5. Force new deployment:
```bash
aws ecs update-service \
  --cluster dev-sentinel-mas \
  --service dev-sentinel-mas-api \
  --force-new-deployment
```

## Step 5: Verify Setup

### Check CloudWatch Logs
```bash
aws logs tail /ecs/dev/sentinel-mas-api --follow
```

### View Dashboard
- Go to: https://console.aws.amazon.com/cloudwatch/home?region=ap-southeast-1#dashboards
- Select: `dev-sentinel-mas`

### View X-Ray Traces
- Go to: https://console.aws.amazon.com/xray/home?region=ap-southeast-1
- Click "Service Map" to see microservices
- Click "Traces" to see individual requests

### Test Alerts
Trigger a high CPU alarm:
```bash
# Generate load to API
for i in {1..1000}; do
  curl https://your-alb-url/api/health &
done
```

Check your email for SNS notifications.

## Step 6: Configure Slack/PagerDuty (Optional)

### Slack Integration

1. Create Slack webhook URL
2. Add SNS subscription:

```bash
aws sns subscribe \
  --topic-arn arn:aws:sns:ap-southeast-1:ACCOUNT:dev-sentinel-mas-alerts \
  --protocol https \
  --notification-endpoint https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

### PagerDuty Integration

1. Get PagerDuty integration key
2. Add SNS subscription:

```bash
aws sns subscribe \
  --topic-arn arn:aws:sns:ap-southeast-1:ACCOUNT:dev-sentinel-mas-alerts \
  --protocol https \
  --notification-endpoint https://events.pagerduty.com/integration/YOUR_KEY/enqueue
```

## Cost Optimization

### Reduce CloudWatch Costs
- Set log retention to 7 days for dev
- Use metric filters to reduce log ingestion
- Sample X-Ray at 5% instead of 100%

### Production Settings
```hcl
# environments/prod/monitoring.tf
module "monitoring" {
  # ... other settings ...
  
  log_retention_days = 30
  cpu_alarm_threshold = 70
  memory_alarm_threshold = 70
}
```

## Troubleshooting

### X-Ray traces not appearing
1. Check X-Ray daemon logs:
```bash
aws logs tail /ecs/dev/xray-daemon --follow
```

2. Verify IAM permissions:
```bash
aws iam get-role-policy --role-name dev-sentinel-mas-api-task --policy-name xray
```

3. Check environment variables in task:
```bash
aws ecs describe-task-definition --task-definition dev-sentinel-mas-api | jq '.taskDefinition.containerDefinitions[0].environment'
```

### Alarms not triggering
1. Verify SNS email subscription is confirmed
2. Check alarm state:
```bash
aws cloudwatch describe-alarms --alarm-names dev-api-cpu-high
```

### Dashboard shows no data
1. Wait 5-10 minutes for metrics to populate
2. Verify services are running:
```bash
aws ecs describe-services --cluster dev-sentinel-mas --services dev-sentinel-mas-api
```

## Next Steps

After Stage 6:
- ✅ Full observability in place
- ✅ Automated alerting configured
- ✅ Distributed tracing enabled

Your Sentinel MAS deployment is now production-ready! 🎉

## Monitoring Checklist

- [ ] CloudWatch dashboards accessible
- [ ] Email alerts confirmed and received
- [ ] X-Ray traces visible in console
- [ ] Log groups created for all services
- [ ] Alarms in OK state
- [ ] SNS topic subscriptions confirmed
- [ ] Application instrumented with X-Ray SDK
- [ ] First traces captured successfully
