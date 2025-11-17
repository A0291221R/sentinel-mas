#!/bin/bash
set -e

echo "🔧 Fixing HTTP Listener Rules"
echo "==============================="

PROJECT="sentinel-v2"
ENV="dev"
REGION="us-east-1"

# Get target group ARNs
echo "📦 Getting target group ARNs..."
API_BLUE=$(aws elbv2 describe-target-groups --names "${PROJECT}-${ENV}-api-blue" --region "$REGION" --query 'TargetGroups[0].TargetGroupArn' --output text)
API_GREEN=$(aws elbv2 describe-target-groups --names "${PROJECT}-${ENV}-api-green" --region "$REGION" --query 'TargetGroups[0].TargetGroupArn' --output text)
UI_BLUE=$(aws elbv2 describe-target-groups --names "${PROJECT}-${ENV}-ui-blue" --region "$REGION" --query 'TargetGroups[0].TargetGroupArn' --output text)
UI_GREEN=$(aws elbv2 describe-target-groups --names "${PROJECT}-${ENV}-ui-green" --region "$REGION" --query 'TargetGroups[0].TargetGroupArn' --output text)
CENTRAL_BLUE=$(aws elbv2 describe-target-groups --names "${PROJECT}-${ENV}-central-blue" --region "$REGION" --query 'TargetGroups[0].TargetGroupArn' --output text)
CENTRAL_GREEN=$(aws elbv2 describe-target-groups --names "${PROJECT}-${ENV}-central-green" --region "$REGION" --query 'TargetGroups[0].TargetGroupArn' --output text)

# Get listener ARN
echo "🎯 Getting listener ARN..."
ALB_ARN=$(aws elbv2 describe-load-balancers --names "${PROJECT}-${ENV}-alb" --region "$REGION" --query 'LoadBalancers[0].LoadBalancerArn' --output text)
LISTENER_ARN=$(aws elbv2 describe-listeners --load-balancer-arn "$ALB_ARN" --region "$REGION" --query 'Listeners[?Port==`80`].ListenerArn' --output text)

echo "Listener ARN: $LISTENER_ARN"

# Get rule ARNs
echo "📋 Getting rule ARNs..."
API_RULE=$(aws elbv2 describe-rules --listener-arn "$LISTENER_ARN" --region "$REGION" --query 'Rules[?Priority==`100`].RuleArn' --output text)
CENTRAL_RULE=$(aws elbv2 describe-rules --listener-arn "$LISTENER_ARN" --region "$REGION" --query 'Rules[?Priority==`101`].RuleArn' --output text)
UI_RULE=$(aws elbv2 describe-rules --listener-arn "$LISTENER_ARN" --region "$REGION" --query 'Rules[?Priority==`200`].RuleArn' --output text)

echo ""
echo "🔧 Fixing API rule (Priority 100: /api/*)..."
aws elbv2 modify-rule \
  --rule-arn "$API_RULE" \
  --region "$REGION" \
  --actions Type=forward,ForwardConfig="{TargetGroups=[{TargetGroupArn=${API_BLUE},Weight=100},{TargetGroupArn=${API_GREEN},Weight=0}]}"
echo "  ✅ API: 100% blue, 0% green"

echo ""
echo "🔧 Fixing Central rule (Priority 101: /tracking/*)..."
aws elbv2 modify-rule \
  --rule-arn "$CENTRAL_RULE" \
  --region "$REGION" \
  --actions Type=forward,ForwardConfig="{TargetGroups=[{TargetGroupArn=${CENTRAL_BLUE},Weight=100},{TargetGroupArn=${CENTRAL_GREEN},Weight=0}]}"
echo "  ✅ Central: 100% blue, 0% green"

echo ""
echo "🔧 Fixing UI rule (Priority 200: /*)..."
aws elbv2 modify-rule \
  --rule-arn "$UI_RULE" \
  --region "$REGION" \
  --actions Type=forward,ForwardConfig="{TargetGroups=[{TargetGroupArn=${UI_BLUE},Weight=100},{TargetGroupArn=${UI_GREEN},Weight=0}]}"
echo "  ✅ UI: 100% blue, 0% green"

echo ""
echo "🔧 Fixing default action..."
aws elbv2 modify-listener \
  --listener-arn "$LISTENER_ARN" \
  --region "$REGION" \
  --default-actions Type=forward,ForwardConfig="{TargetGroups=[{TargetGroupArn=${UI_BLUE},Weight=100},{TargetGroupArn=${UI_GREEN},Weight=0}]}"
echo "  ✅ Default: 100% blue, 0% green"

echo ""
echo "✅ All HTTP listener rules fixed!"
echo ""
echo "🔍 Verifying..."
aws elbv2 describe-rules --listener-arn "$LISTENER_ARN" --region "$REGION" \
  --query 'Rules[?Priority!=`null`].[Priority,Actions[0].ForwardConfig.TargetGroups[*].[TargetGroupArn,Weight]]' \
  --output table