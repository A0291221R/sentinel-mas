#!/bin/bash

fetch_ssm_config() {
    local param_path=$1
    local param_name=$2
    
    echo "📥 Fetching $param_name..."
    
    if aws sts get-caller-identity &>/dev/null; then
        CONFIG=$(aws ssm get-parameter \
            --name "$param_path" \
            --with-decryption \
            --query 'Parameter.Value' \
            --output text 2>/dev/null)
        
        if [ $? -eq 0 ] && [ -n "$CONFIG" ]; then
            # Convert spaces to newlines if no newlines exist
            if [[ "$CONFIG" != *$'\n'* ]]; then
                CONFIG=$(echo "$CONFIG" | tr ' ' '\n')
            fi
            
            # Export each key=value pair
            while IFS='=' read -r key value; do
                [ -n "$key" ] && export "$key=$value"
            done <<< "$CONFIG"
            
            echo "✅ Loaded $param_name"
            return 0
        else
            echo "⚠️  Could not fetch $param_name"
            return 1
        fi
    else
        echo "⚠️  No AWS credentials for $param_name"
        return 1
    fi
}

if [ "$ENVIRONMENT" = "production" ] || [ "$ENVIRONMENT" = "staging" ]; then
    echo "🔐 Fetching configuration from AWS SSM Parameter Store..."
    
    # Fetch all three configs
    fetch_ssm_config "/sentinel-mas/shared/config" "shared config"
    fetch_ssm_config "/sentinel-mas/sentinel/config" "sentinel config"
    fetch_ssm_config "/sentinel-mas/api/config" "api config"

elif [ "$ENVIRONMENT" = "test" ]; then
    echo "🧪 Test environment - using provided environment variables"
    
else
    echo "🔧 Development environment - checking for .env files"

    # Load local .env files if they exist
    [ -f .env.shared ] && source .env.shared && echo "✅ Loaded .env.shared"
    [ -f .env.sentinel ] && source .env.sentinel && echo "✅ Loaded .env.sentinel"
    [ -f .env.api ] && source .env.api && echo "✅ Loaded .env.api"
fi

echo "✅ Configuration ready"
echo "🌐 Starting uvicorn..."

# If no command provided, use default
if [ $# -eq 0 ]; then
    echo "🚀 Starting uvicorn with default command..."
    exec uvicorn api_service.main:app --host 0.0.0.0 --port ${API_PORT:-8000}
else
    echo "🚀 Executing command: $@"
    exec "$@"
fi

