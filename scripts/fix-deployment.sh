#!/bin/bash
set -e

echo "🔧 Fixing the failed deployment rule..."

RULE_ARN="arn:aws:elasticloadbalancing:us-east-1:590183890857:listener-rule/app/sentinel-v2-dev-alb/59a4cf5d39ad4335/2d62be71ce5a6dd3/ab47b4413056af0e"

# Get target group ARNs (assuming this is API based on the error)
BLUE_TG=$(aws elbv2 describe-target-groups \
  --names "sentinel-v2-dev-api-blue" \
  --query 'TargetGroups[0].TargetGroupArn' \
  --output text)

GREEN_TG=$(aws elbv2 describe-target-groups \
  --names "sentinel-v2-dev-api-green" \
  --query 'TargetGroups[0].TargetGroupArn' \
  --output text)

echo "📊 Current state:"
aws elbv2 describe-rules \
  --rule-arns "$RULE_ARN" \
  --query 'Rules[0].Actions[0].ForwardConfig.TargetGroups[*].[TargetGroupArn,Weight]' \
  --output table

echo ""
echo "🔄 Resetting to 100% blue, 0% green..."
aws elbv2 modify-rule \
  --rule-arn "$RULE_ARN" \
  --actions Type=forward,ForwardConfig="{TargetGroups=[{TargetGroupArn=${BLUE_TG},Weight=100},{TargetGroupArn=${GREEN_TG},Weight=0}]}"

echo ""
echo "✅ Fixed! New state:"
aws elbv2 describe-rules \
  --rule-arns "$RULE_ARN" \
  --query 'Rules[0].Actions[0].ForwardConfig.TargetGroups[*].[TargetGroupArn,Weight]' \
  --output table

echo ""
echo "🚀 You can now retry your deployment"