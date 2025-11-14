# Sentinel Frontend - Solution 3: Nginx Proxy Setup

This setup uses nginx as a reverse proxy to avoid hardcoding API URLs in the frontend code, which prevents SonarQube security violations.

## Architecture

```
Browser → Nginx (port 80) → Backend API
         ↓
    Frontend Files
    (index.html, etc.)
```

- Frontend makes requests to `/api/*` (relative URLs)
- Nginx proxies `/api/*` to the actual backend API URL
- No hardcoded URLs in JavaScript code ✅
- No SonarQube violations ✅

## Files Overview

1. **Dockerfile** - Builds the nginx container with template support
2. **nginx.conf.template** - Nginx configuration with environment variable placeholders
3. **index.html** - Updated to use relative API paths (`/api` instead of full URLs)
4. **docker-compose.yml** - Example for local testing

## Local Testing

### Option 1: Using Docker Compose

```bash
# Update the API_URL in docker-compose.yml first
docker-compose up --build
```

### Option 2: Using Docker directly

```bash
# Build the image
docker build -t sentinel-frontend .

# Run with environment variables
docker run -p 80:80 \
  -e API_URL=http://your-backend-api:8000 \
  -e TRACKING_API_URL=http://sentinel-central:8100 \
  sentinel-frontend
```

### Option 3: For local development

If testing locally and your API is on localhost:8000:

```bash
docker run -p 80:80 \
  -e API_URL=http://host.docker.internal:8000 \
  -e TRACKING_API_URL=http://host.docker.internal:8100 \
  sentinel-frontend
```

Then access at: http://localhost

## AWS ECS Deployment

### 1. Build and Push to ECR

```bash
# Authenticate to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com

# Build image
docker build -t sentinel-frontend .

# Tag image
docker tag sentinel-frontend:latest YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/sentinel-frontend:latest

# Push to ECR
docker push YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/sentinel-frontend:latest
```

### 2. Update ECS Task Definition

In your ECS Task Definition JSON, add environment variables to the container definition:

```json
{
  "family": "sentinel-mas-dev-frontend",
  "containerDefinitions": [
    {
      "name": "sentinel-frontend",
      "image": "YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/sentinel-frontend:latest",
      "portMappings": [
        {
          "containerPort": 80,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "API_URL",
          "value": "http://sentinel-mas-dev-api.internal:8000"
        },
        {
          "name": "TRACKING_API_URL",
          "value": "http://sentinel-central.internal:8100"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/sentinel-mas-dev-frontend",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "wget --quiet --tries=1 --spider http://localhost/health || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 10
      }
    }
  ],
  "requiresCompatibilities": ["FARGATE"],
  "networkMode": "awsvpc",
  "cpu": "256",
  "memory": "512",
  "taskRoleArn": "arn:aws:iam::YOUR_ACCOUNT_ID:role/sentinel-mas-ecs-task-role",
  "executionRoleArn": "arn:aws:iam::YOUR_ACCOUNT_ID:role/ecsTaskExecutionRole"
}
```

### 3. Via AWS Console (Easier)

1. **Go to ECS Dashboard** → Task Definitions
2. Select your task definition → **Create new revision**
3. Scroll to **Container Definitions** → Click on your container
4. Under **Environment variables**, add:
   - Key: `API_URL`, Value: `http://your-backend-service:8000`
   - Key: `TRACKING_API_URL`, Value: `http://sentinel-central:8100`
5. Click **Update** → **Create**

### 4. Update ECS Service

```bash
aws ecs update-service \
  --cluster sentinel-mas-dev \
  --service sentinel-mas-dev-ui \
  --task-definition sentinel-mas-dev-ui:NEW_REVISION \
  --force-new-deployment
```

## Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `API_URL` | Backend API endpoint | `http://api-service:8000` |
| `TRACKING_API_URL` | Tracking service endpoint | `http://sentinel-central:8100` |

**Note:** For ECS services within the same VPC:
- Use service discovery names (e.g., `http://sentinel-mas-dev-api:8000`)
- Or use internal ALB/NLB DNS names
- Or use private IP addresses

## How It Works

1. **Build Time:**
   - Dockerfile copies `nginx.conf.template` to `/etc/nginx/templates/`
   - No hardcoded URLs in the code

2. **Container Start:**
   - Nginx reads environment variables (`API_URL`, `TRACKING_API_URL`)
   - Automatically processes `.template` files and substitutes `${API_URL}` with actual values
   - Creates final nginx config in `/etc/nginx/conf.d/`

3. **Runtime:**
   - User accesses frontend at `http://your-domain.com`
   - JavaScript makes request to `/api/v1/queries`
   - Nginx proxies to `${API_URL}/v1/queries`
   - Response sent back to browser

## Benefits

✅ **No SonarQube violations** - No hardcoded URLs in code
✅ **Secure** - API URLs hidden from browser/frontend code
✅ **Flexible** - Change backend URLs via environment variables
✅ **CORS handling** - Nginx handles cross-origin requests
✅ **Single domain** - Frontend and API appear on same origin

## Troubleshooting

### Check if environment variables are set:

```bash
# Inside the container
docker exec -it <container-id> env | grep API_URL
```

### Check generated nginx config:

```bash
# Inside the container
docker exec -it <container-id> cat /etc/nginx/conf.d/default.conf
```

### Test API proxy:

```bash
# From your local machine
curl http://localhost/api/health
```

### View nginx logs:

```bash
# ECS CloudWatch Logs
aws logs tail /ecs/sentinel-mas-dev-frontend --follow

# Docker logs
docker logs <container-id>
```

## Security Notes

- API URLs are only visible in ECS Task Definition (infrastructure level)
- Not exposed in frontend JavaScript code
- Not visible in browser DevTools/Network tab
- Can add additional nginx security headers if needed

## Next Steps

1. ✅ Update your ECS Task Definition with environment variables
2. ✅ Rebuild and push Docker image to ECR
3. ✅ Update ECS service to use new task definition revision
4. ✅ Verify the application works correctly
5. ✅ Run SonarQube scan to confirm no violations

## Support

If you encounter issues:
1. Check nginx logs in CloudWatch
2. Verify environment variables are set correctly in task definition
3. Ensure backend services are reachable from the frontend container
4. Check security groups allow traffic between services
