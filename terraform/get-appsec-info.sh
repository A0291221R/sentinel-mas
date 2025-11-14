#!/bin/bash
# Save this as: get-appspec-info.sh
PROJECT_NAME="sentinel-v2"
ENVIRONMENT="dev"  # Change to "prod" for production
CLUSTER_NAME="${PROJECT_NAME}-${ENVIRONMENT}-cluster"

echo "================================================"
echo "🔍 Retrieving AppSpec Configuration Info"
echo "Environment: $ENVIRONMENT"
echo "================================================"
echo ""

# 1. Get ECS Cluster Info
echo "📦 ECS CLUSTER INFO:"
aws ecs describe-clusters \
  --clusters $CLUSTER_NAME \
  --query 'clusters[0].[clusterName,status]' \
  --output table

# 2. Get VPC & Subnets
echo ""
echo "🌐 VPC & SUBNETS:"
VPC_ID=$(aws ec2 describe-vpcs \
  --filters "Name=tag:Environment,Values=$ENVIRONMENT" \
  --query 'Vpcs[0].VpcId' \
  --output text)

echo "VPC ID: $VPC_ID"
echo ""
echo "Available Subnets:"
aws ec2 describe-subnets \
  --filters "Name=vpc-id,Values=$VPC_ID" \
  --query 'Subnets[].[SubnetId,AvailabilityZone,CidrBlock,Tags[?Key==`Name`].Value|[0]]' \
  --output table

# 3. Get Security Groups
echo ""
echo "🔒 SECURITY GROUPS:"
aws ec2 describe-security-groups \
  --filters "Name=vpc-id,Values=$VPC_ID" \
  --query 'SecurityGroups[].[GroupId,GroupName,Description]' \
  --output table

# 4. Get ECS Service Details
echo ""
echo "📡 ECS SERVICE INFO:"
for SERVICE in api ui central; do
  echo "Service: ${PROJECT_NAME}-${ENVIRONMENT}-${SERVICE}"
  aws ecs describe-services \
    --cluster $CLUSTER_NAME \
    --services "${PROJECT_NAME}-${SERVICE}-service-${ENVIRONMENT}" \
    --query 'services[0].networkConfiguration.awsvpcConfiguration.[subnets,securityGroups]' \
    --output json 2>/dev/null || echo "  Service not found"
  echo ""
done

# 5. Get Target Groups
echo ""
echo "🎯 APPLICATION LOAD BALANCER TARGET GROUPS:"
aws elbv2 describe-target-groups \
  --query 'TargetGroups[].[TargetGroupName,TargetGroupArn,Port,Protocol]' \
  --output table

# 6. Create AppSpec Template
echo ""
echo "================================================"
echo "📝 APPSPEC CONFIGURATION SUMMARY"
echo "================================================"

# Get first two subnets
SUBNET_1=$(aws ec2 describe-subnets \
  --filters "Name=vpc-id,Values=$VPC_ID" \
  --query 'Subnets[0].SubnetId' \
  --output text)

SUBNET_2=$(aws ec2 describe-subnets \
  --filters "Name=vpc-id,Values=$VPC_ID" \
  --query 'Subnets[1].SubnetId' \
  --output text)

# Get ECS security group
SG_ID=$(aws ec2 describe-security-groups \
  --filters "Name=vpc-id,Values=$VPC_ID" "Name=group-name,Values=*ecs*" \
  --query 'SecurityGroups[0].GroupId' \
  --output text)

echo ""
echo "✅ Use these values in your AppSpec files:"
echo ""
echo "Subnets:"
echo "  - $SUBNET_1"
echo "  - $SUBNET_2"
echo ""
echo "SecurityGroups:"
echo "  - $SG_ID"
echo ""
echo "================================================"