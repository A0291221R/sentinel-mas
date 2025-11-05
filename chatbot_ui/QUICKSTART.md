# Quick Start Guide - Sentinel Frontend with Nginx Proxy

## What Changed?

### Before (Had SonarQube Issues):
```javascript
const API_BASE_URL = process.env.API_URL || 'http://localhost:8000'; // ❌ Hardcoded URL
```

### After (SonarQube Compliant):
```javascript
const API_BASE_URL = '/api'; // ✅ Relative URL proxied by nginx
```

## Files You Need

1. ✅ `Dockerfile` - Updated to use nginx templates
2. ✅ `nginx.conf.template` - Nginx config with `${API_URL}` placeholders
3. ✅ `index.html` - Changed to use `/api` instead of full URL
4. ✅ `example-prompts.json` - (Keep your existing file)

## Deployment Steps

### Step 1: Build and Push to ECR

```bash
# Replace with your values
ACCOUNT_ID="123456789012"
REGION="us-east-1"
REPO_NAME="sentinel-frontend"

# Authenticate
aws ecr get-login-password --region $REGION | \
  docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com

# Build
docker build -t $REPO_NAME .

# Tag
docker tag $REPO_NAME:latest $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$REPO_NAME:latest

# Push
docker push $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$REPO_NAME:latest
```

### Step 2: Update ECS Task Definition (AWS Console)

1. Go to **ECS** → **Task Definitions**
2. Select your task → **Create new revision**
3. Click on the container name
4. Scroll to **Environment variables** section
5. Add these variables:

| Key | Value |
|-----|-------|
| `API_URL` | `http://your-backend-service-name:8000` |
| `TRACKING_API_URL` | `http://sentinel-central:8100` |

6. Update the **Image** to your new ECR image
7. Click **Update** → **Create**

### Step 3: Deploy to ECS Service

```bash
# Update service with new task definition
aws ecs update-service \
  --cluster sentinel-mas-dev \
  --service sentinel-mas-dev-frontend \
  --force-new-deployment
```

Or via AWS Console:
1. **ECS** → **Clusters** → Your cluster
2. Select service → **Update service**
3. Check **Force new deployment**
4. Click **Update**

## Verify Deployment

### Check if container is running:
```bash
aws ecs list-tasks --cluster sentinel-mas-dev --service-name sentinel-mas-dev-frontend
```

### Check logs:
```bash
aws logs tail /ecs/sentinel-mas-dev-frontend --follow
```

### Test the application:
```bash
# Replace with your actual ALB/domain
curl http://your-frontend-url.com/health
# Should return: healthy

curl http://your-frontend-url.com/api/v1/health
# Should proxy to backend and return API health status
```

## Important Notes

### Backend Service Names

Your `API_URL` should be the **internal** service name or DNS within your VPC:

**If using ECS Service Discovery:**
```
API_URL=http://sentinel-mas-dev-api.local:8000
```

**If using ALB:**
```
API_URL=http://internal-sentinel-api-alb-123456.us-east-1.elb.amazonaws.com
```

**If using direct container IP (not recommended):**
```
API_URL=http://10.0.1.50:8000
```

### Security Groups

Ensure your frontend security group allows **outbound** traffic to your backend service:
- Protocol: TCP
- Port: 8000 (or your backend port)
- Destination: Backend security group

And backend security group allows **inbound** from frontend:
- Protocol: TCP
- Port: 8000
- Source: Frontend security group

## Rollback Plan

If something goes wrong:

```bash
# Rollback to previous task definition
aws ecs update-service \
  --cluster sentinel-mas-dev \
  --service sentinel-mas-dev-frontend \
  --task-definition sentinel-mas-dev-frontend:PREVIOUS_REVISION
```

## Testing Locally First

Before deploying to AWS, test locally:

```bash
# Terminal 1: Run your backend API (or use a test API)
# Assuming it's running on localhost:8000

# Terminal 2: Run frontend container
docker build -t sentinel-frontend .
docker run -p 8080:80 \
  -e API_URL=http://host.docker.internal:8000 \
  -e TRACKING_API_URL=http://host.docker.internal:8100 \
  sentinel-frontend

# Terminal 3: Test
curl http://localhost:8080/health
curl http://localhost:8080/api/v1/health
```

Open browser: http://localhost:8080

## Checklist

- [ ] Updated `index.html` with `/api` instead of `process.env.API_URL`
- [ ] Created `nginx.conf.template` with `${API_URL}` placeholder
- [ ] Updated `Dockerfile` to use nginx templates
- [ ] Built and pushed image to ECR
- [ ] Updated ECS task definition with environment variables
- [ ] Updated ECS service to use new task definition
- [ ] Verified security groups allow communication
- [ ] Tested application in browser
- [ ] Checked CloudWatch logs for errors
- [ ] Ran SonarQube scan (should pass now!)

## Common Issues

### 1. "API service unavailable" error
- Check if backend service is running
- Verify security groups allow traffic
- Check `API_URL` environment variable is correct

### 2. Nginx shows 502 Bad Gateway
- Backend service is down or unreachable
- Check ECS service status of backend
- Verify service discovery DNS is resolving

### 3. Environment variables not working
- Ensure you're using `.template` extension
- Check nginx logs: `aws logs tail /ecs/sentinel-mas-dev-frontend`
- Verify variables are set in task definition

## Support

Need help? Check:
1. CloudWatch Logs: `/ecs/sentinel-mas-dev-frontend`
2. ECS Task events in AWS Console
3. Security group rules
4. Backend service health

## Success Criteria

✅ Frontend loads in browser
✅ API requests work (check Network tab)
✅ No hardcoded URLs in JavaScript
✅ SonarQube scan passes
✅ No "process is not defined" errors



cd services/chatbot_ui

# Build
docker build -t sentinel-mas-ui:latest .

# Get account and login
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com

# Push
docker tag sentinel-mas-ui:latest $ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/sentinel-mas-ui:latest
docker push $ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/sentinel-mas-ui:latest

# Deploy
aws ecs update-service \
  --cluster sentinel-mas-dev-cluster \
  --service sentinel-mas-dev-ui \
  --force-new-deployment