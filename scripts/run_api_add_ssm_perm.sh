#!/bin/bash

# Get task role name
TASK_ROLE=$(aws ecs describe-task-definition \
  --task-definition sentinel-mas-dev-api \
  --query 'taskDefinition.taskRoleArn' \
  --output text | cut -d'/' -f2)

echo "Task Role: $TASK_ROLE"

# Add SSM policy
aws iam put-role-policy \
  --role-name $TASK_ROLE \
  --policy-name SSMParameterAccess \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Action": [
        "ssm:GetParameter",
        "ssm:GetParameters"
      ],
      "Resource": "arn:aws:ssm:us-east-1:*:parameter/sentinel-mas/*"
    }]
  }'

# Restart service
aws ecs update-service \
  --cluster sentinel-mas-dev-cluster \
  --service sentinel-mas-dev-api \
  --force-new-deployment