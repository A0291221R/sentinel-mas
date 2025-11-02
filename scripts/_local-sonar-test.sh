#!/bin/bash

# Exit on error
set -e

echo "🧪 Running tests with coverage..."
uv sync --all-extras --dev
mkdir -p test-results
uv run pytest \
  --junitxml=test-results/junit-3.12.xml \
  --cov=sentinel_mas \
  --cov-report=xml:test-results/coverage-3.12.xml

echo "✅ Tests completed!"
echo ""
echo "📊 Running SonarQube analysis..."

# Check if SONAR_TOKEN is set
if [ -z "$SONAR_TOKEN" ]; then
    echo "❌ Error: SONAR_TOKEN environment variable is not set"
    echo "Set it with: export SONAR_TOKEN='your-token-here'"
    exit 1
fi

if [ -z "$SONAR_HOST_URL" ]; then
    echo "❌ Error: SONAR_HOST_URL environment variable is not set"
    echo "Set it with: export SONAR_HOST_URL='https://sonarcloud.io'"
    exit 1
fi

# Run SonarScanner
if [[ "$OSTYPE" == "msys" ]]; then
    cmd //c sonar-scanner.bat "$@"
else
    sonar-scanner "$@"
fi

echo "✅ SonarQube analysis completed!"
echo "Check your results at: $SONAR_HOST_URL/dashboard?id=A0291221R_sentinel-mas"