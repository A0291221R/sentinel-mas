#!/bin/bash
set -e

echo "🚀 Starting API service..."

ENVIRONMENT=${ENVIRONMENT:-development}
echo "📍 Environment: $ENVIRONMENT"

if [ "$ENVIRONMENT" = "production" ] || [ "$ENVIRONMENT" = "staging" ]; then
    echo "🔐 Fetching configuration from AWS SSM Parameter Store..."
    
    python3 << EOF
import boto3
import sys

try:
    ssm = boto3.client('ssm', region_name='${AWS_REGION:-us-east-1}')
    
    # Fetch and write all 3 config files to /app (working directory)
    configs = {
        '/sentinel-mas/api/config': '.env.api',
        '/sentinel-mas/sentinel/config': '.env.sentinel',
        '/sentinel-mas/shared/config': '.env.shared'
    }
    
    for param_name, file_name in configs.items():
        print(f"📥 Fetching {param_name}...")
        response = ssm.get_parameter(Name=param_name, WithDecryption=True)
        with open(file_name, 'w') as f:
            f.write(response['Parameter']['Value'])
        print(f"✅ {file_name} created")
    
except Exception as e:
    print(f"❌ Error fetching secrets: {e}", file=sys.stderr)
    sys.exit(1)
EOF
    
    echo "✅ All configurations loaded from AWS SSM"
else
    echo "🔧 Using local development configuration"
    echo "⚠️  Make sure you have .env.api, .env.sentinel, and .env.shared files!"
    echo "⚠️  Copy from examples: cp .env.*.example .env.*"

     # Check if required .env files exist
    MISSING_FILES=()
    
    if [ ! -f ".env.api" ]; then
        MISSING_FILES+=(".env.api")
    fi
    
    if [ ! -f ".env.sentinel" ]; then
        MISSING_FILES+=(".env.sentinel")
    fi
    
    if [ ! -f ".env.shared" ]; then
        MISSING_FILES+=(".env.shared")
    fi
    
    if [ ${#MISSING_FILES[@]} -gt 0 ]; then
        echo "❌ ERROR: Missing required configuration files:"
        for file in "${MISSING_FILES[@]}"; do
            echo "   - $file"
        done
        echo ""
        echo "⚠️  Please create these files or mount them as volumes"
        echo "⚠️  Example: cp .env.*.example .env.*"
        echo ""
        exit 1
    fi
    
    echo "✅ All configuration files found:"
    echo "   - .env.api ($(wc -l < .env.api) lines)"
    echo "   - .env.sentinel ($(wc -l < .env.sentinel) lines)"
    echo "   - .env.shared ($(wc -l < .env.shared) lines)"
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