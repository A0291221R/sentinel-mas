#!/bin/bash
#
# Wait for CodeDeploy deployment to complete
# Usage: ./wait-for-deployment.sh <application-name> <deployment-id> <timeout-minutes>
#

set -e

APPLICATION_NAME=$1
DEPLOYMENT_ID=$2
TIMEOUT_MINUTES=${3:-30}
CHECK_INTERVAL=15  # seconds

if [[ -z "$APPLICATION_NAME" ]] || [[ -z "$DEPLOYMENT_ID" ]]; then
    echo "Usage: $0 <application-name> <deployment-id> [timeout-minutes]"
    exit 1
fi

echo "📊 Monitoring deployment: ${DEPLOYMENT_ID}"
echo "⏱️  Timeout: ${TIMEOUT_MINUTES} minutes"
echo ""

START_TIME=$(date +%s)
TIMEOUT_SECONDS=$((TIMEOUT_MINUTES * 60))

# Function to get deployment status with retry
get_deployment_status() {
    local RETRIES=3
    local RETRY_COUNT=0
    
    while [ $RETRY_COUNT -lt $RETRIES ]; do
        if STATUS=$(aws deploy get-deployment \
            --deployment-id "$DEPLOYMENT_ID" \
            --query 'deploymentInfo.status' \
            --output text 2>/dev/null); then
            echo "$STATUS"
            return 0
        fi
        
        RETRY_COUNT=$((RETRY_COUNT + 1))
        echo "⚠️  API call failed, retrying ($RETRY_COUNT/$RETRIES)..." >&2
        sleep 2
    done
    
    echo "ERROR" >&2
    return 1
}

# Function to get deployment details
get_deployment_info() {
    aws deploy get-deployment \
        --deployment-id "$DEPLOYMENT_ID" \
        --output json
}

# Function to print deployment progress
print_progress() {
    local INFO=$1
    local STATUS=$(echo "$INFO" | jq -r '.deploymentInfo.status')
    local CREATOR=$(echo "$INFO" | jq -r '.deploymentInfo.creator // "Unknown"')
    local START=$(echo "$INFO" | jq -r '.deploymentInfo.createTime // "Unknown"')
    
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🔄 Status: ${STATUS}"
    echo "👤 Creator: ${CREATOR}"
    echo "🕐 Started: ${START}"
    
    # Show target instances/tasks
    if echo "$INFO" | jq -e '.deploymentInfo.targetInstances' > /dev/null 2>&1; then
        local PENDING=$(echo "$INFO" | jq -r '.deploymentInfo.targetInstances.pendingCount // 0')
        local IN_PROGRESS=$(echo "$INFO" | jq -r '.deploymentInfo.targetInstances.inProgressCount // 0')
        local SUCCEEDED=$(echo "$INFO" | jq -r '.deploymentInfo.targetInstances.succeededCount // 0')
        local FAILED=$(echo "$INFO" | jq -r '.deploymentInfo.targetInstances.failedCount // 0')
        
        echo ""
        echo "📈 Target Progress:"
        echo "   ⏳ Pending: ${PENDING}"
        echo "   🔄 In Progress: ${IN_PROGRESS}"
        echo "   ✅ Succeeded: ${SUCCEEDED}"
        echo "   ❌ Failed: ${FAILED}"
    fi
    
    # Show lifecycle events
    if echo "$INFO" | jq -e '.deploymentInfo.deploymentOverview' > /dev/null 2>&1; then
        echo ""
        echo "🎯 Lifecycle Events:"
        echo "$INFO" | jq -r '.deploymentInfo.deploymentOverview | to_entries[] | "   \(.key): \(.value)"'
    fi
    
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
}

# Main monitoring loop
while true; do
    CURRENT_TIME=$(date +%s)
    ELAPSED=$((CURRENT_TIME - START_TIME))
    
    if [[ $ELAPSED -gt $TIMEOUT_SECONDS ]]; then
        echo "❌ Deployment timed out after ${TIMEOUT_MINUTES} minutes"
        exit 1
    fi
    
    INFO=$(get_deployment_info)
    STATUS=$(echo "$INFO" | jq -r '.deploymentInfo.status')
    
    case "$STATUS" in
        "Created"|"Queued"|"InProgress")
            print_progress "$INFO"
            echo "⏳ Deployment in progress... (${ELAPSED}s elapsed)"
            sleep $CHECK_INTERVAL
            ;;
        "Succeeded")
            print_progress "$INFO"
            echo "✅ Deployment completed successfully!"
            
            # Show deployment summary
            DURATION=$(echo "$INFO" | jq -r '.deploymentInfo.completeTime // empty' | xargs -I{} date -d {} +%s)
            if [[ -n "$DURATION" ]]; then
                START_TS=$(echo "$INFO" | jq -r '.deploymentInfo.createTime' | xargs -I{} date -d {} +%s)
                TOTAL_TIME=$((DURATION - START_TS))
                echo "⏱️  Total deployment time: ${TOTAL_TIME} seconds"
            fi
            
            exit 0
            ;;
        "Failed"|"Stopped")
            print_progress "$INFO"
            echo "❌ Deployment failed or was stopped"
            
            # Get error information
            ERROR_INFO=$(echo "$INFO" | jq -r '.deploymentInfo.errorInformation // empty')
            if [[ -n "$ERROR_INFO" ]]; then
                echo ""
                echo "🔍 Error Details:"
                echo "$ERROR_INFO" | jq '.'
            fi
            
            exit 1
            ;;
        "Ready")
            echo "⏸️  Deployment is ready but not started"
            sleep $CHECK_INTERVAL
            ;;
        *)
            echo "⚠️  Unknown deployment status: ${STATUS}"
            sleep $CHECK_INTERVAL
            ;;
    esac
done
