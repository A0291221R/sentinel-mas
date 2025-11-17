# Stage 6 Quick Reference

## 📦 What You Got

### Terraform Modules
- `modules/monitoring/` - CloudWatch logs, dashboards, alarms, SNS
- `modules/xray/` - X-Ray tracing, sampling rules, IAM policies

### Documentation
- `STAGE6-IMPLEMENTATION.md` - Full deployment guide
- `docs/xray-instrumentation-nodejs.md` - Application code examples

### Example Files
- `terraform/xray-sidecar-example.tf` - ECS task with X-Ray sidecar

## ⚡ Quick Deploy

```bash
# 1. Copy modules to your terraform directory
cp -r stage6/terraform/modules/* terraform/modules/

# 2. Add monitoring to your environment
cat > terraform/environments/dev/monitoring.tf << 'EOF'
module "monitoring" {
  source = "../../modules/monitoring"
  environment = "dev"
  cluster_name = module.ecs.cluster_name
  alb_arn_suffix = module.alb.alb_arn_suffix
  db_instance_id = module.rds.db_instance_id
  alert_emails = ["your-email@example.com"]
}

module "xray" {
  source = "../../modules/xray"
  environment = "dev"
  api_task_role_name = module.ecs.api_task_role_name
  ui_task_role_name = module.ecs.ui_task_role_name
  central_task_role_name = module.ecs.central_task_role_name
}
EOF

# 3. Deploy
cd terraform/environments/dev
terraform init
terraform apply

# 4. Instrument your Node.js apps
npm install aws-xray-sdk-core aws-xray-sdk-express

# 5. Add to your app.js (see docs for details)
```

## 📊 Key Metrics Monitored

| Metric | Threshold | Alert |
|--------|-----------|-------|
| CPU Usage | >80% | SNS Email |
| Memory Usage | >80% | SNS Email |
| 5XX Errors | >10 in 5min | SNS Email |
| Response Time | >2 seconds | SNS Email |
| RDS CPU | >80% | SNS Email |
| RDS Storage | <10GB | SNS Email |

## 🔍 X-Ray Sampling

- **Default**: 5% of all requests
- **Errors**: 100% of failed requests
- **Cost**: ~$5-10/month for dev

## 💰 Cost Summary

**Dev Environment**: ~$15-30/month
**Production**: ~$60-160/month

## 🎯 Access URLs

```bash
# CloudWatch Dashboard
https://console.aws.amazon.com/cloudwatch/home?region=ap-southeast-1#dashboards

# X-Ray Service Map
https://console.aws.amazon.com/xray/home?region=ap-southeast-1#/service-map

# CloudWatch Logs
https://console.aws.amazon.com/cloudwatch/home?region=ap-southeast-1#logsV2:log-groups
```

## 🚨 Common Issues

**No X-Ray traces?**
- Check IAM permissions
- Verify X-Ray daemon is running
- Confirm environment variables are set

**No email alerts?**
- Confirm SNS subscription via email link
- Check spam folder

**Dashboard empty?**
- Wait 5-10 minutes for initial metrics
- Verify ECS services are running

## 📞 Support

- Implementation Guide: `STAGE6-IMPLEMENTATION.md`
- X-Ray Code Examples: `docs/xray-instrumentation-nodejs.md`
- Terraform Examples: `terraform/xray-sidecar-example.tf`
