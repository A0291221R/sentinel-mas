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
fi

echo "✅ Configuration ready"
echo "🌐 Starting uvicorn..."

exec "$@"