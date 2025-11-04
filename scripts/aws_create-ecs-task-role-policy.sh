#!/bin/bash
# Create IAM role

aws iam create-role \
  --role-name sentinel-mas-ecs-task-role \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {"Service": "ecs-tasks.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }]
  }'

# Attach policy
aws iam put-role-policy \
  --role-name sentinel-mas-ecs-task-role \
  --policy-name ssm-access \
  --policy-document file://ecs-task-role-policy.json