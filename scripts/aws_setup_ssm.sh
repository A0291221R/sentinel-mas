#!/bin/bash

# Set your AWS region
export AWS_REGION=us-east-1

# Store API config
aws ssm put-parameter \
  --name " /sentinel-mas/api/config" \
  --value "$(cat .env.api.aws)" \
  --type "SecureString" \
  --description "API service configuration" \
  --overwrite \
  --region $AWS_REGION

# Store shared config
aws ssm put-parameter \
  --name " /sentinel-mas/shared/config" \
  --value "$(cat .env.shared.aws)" \
  --type "SecureString" \
  --description "Shared configuration" \
  --overwrite \
  --region $AWS_REGION

# Store sentinel config
aws ssm put-parameter \
  --name " /sentinel-mas/sentinel/config" \
  --value "$(cat .env.sentinel.aws)" \
  --type "SecureString" \
  --description "sentinel configuration" \
  --overwrite \
  --region $AWS_REGION


# Verify
aws ssm get-parameter \
  --name " /sentinel-mas/sentinel/config" \
  --with-decryption \
  --region $AWS_REGION