#!/bin/bash

echo "Setting up Python 3.12 development environment..."

# Create virtual environment
# python3.12 -m venv .venv
uv venv .venv
source .venv/bin/activate

# Upgrade pip
uv run pip install --upgrade pip

# Install dependencies
uv run pip install -r requirements.txt

# Create test directories
mkdir -p test-results

echo "✅ Development environment ready!"
echo "🔧 Activate with: source .venv/bin/activate"
echo "🧪 Run tests with: pytest"
echo "📝 Run linting with: ./scripts/lint.sh"