#!/bin/bash

set -e

echo "🚀 Starting linting process..."

# Mypy configuration
CHECK_PATHS="sentinel_mas api_service tests"
MYPY_CONFIG="--count --show-source --format='::error file=%(path)s,line=%(row)d,col=%(col)d::%(code)s: %(text)s' --python-version 3.12"
run_linter() {
    local name=$1
    local check_cmd=$2
    local fix_cmd=$3
    
    echo "--- Running $name ---"
    
    if [ "$1" = "mypy" ]; then
        # Use custom config for mypy
        check_cmd="mypy $CHECK_PATHS $MYPY_CONFIG"
    fi
    
    if [ "$FIX_MODE" = true ] && [ "$1" != "mypy" ] && [ "$1" != "flake8" ]; then
        eval $fix_cmd
        echo "✅ $name applied fixes"
    else
        if eval $check_cmd; then
            echo "✅ $name passed"
        else
            echo "❌ $name failed"
            return 1
        fi
    fi
}

# Check if fix mode is enabled
FIX_MODE=false
if [ "$1" = "--fix" ]; then
    FIX_MODE=true
    echo "🔧 Running in FIX mode"
fi

run_linter "Black" "black --check ." "black $CHECK_PATHS" &
run_linter "isort" "isort --check-only ." "isort $CHECK_PATHS" &
run_linter "flake8" "flake8 $CHECK_PATHS --count --show-source --statistics" "echo 'flake8: fix errors manually'" &
run_linter "mypy" "mypy $CHECK_PATHS $MYPY_CONFIG" "echo 'mypy: fix errors manually'" &

wait

echo ""
if [ "$FIX_MODE" = true ]; then
    echo "🎉 All fixes applied!"
else
    echo "🎉 Linting completed!"
fi