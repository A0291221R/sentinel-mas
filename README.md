# Sentinel-MAS Unit Tests (pytest)

## How to run

1. Ensure your source tree looks like this (package directory name matters):

```
<repo-root>/
  sentinel_mas/
    policy_sentinel/
    tools/
    agents/
    app/
    ...
  tests/
```

2. Copy the `tests/` folder from this bundle into your repo root so that `tests/` sits next to the `sentinel_mas/` folder.

3. (Recommended) Create a virtualenv and install test deps:
```
pip install -r requirements-test.txt
```

4. Run tests with coverage:
```
pip install -e .[test]
pytest --cov=sentinel_mas --cov-report=term-missing


```

If your package directory is not named `sentinel_mas`, either rename it or update the imports inside the tests accordingly.


### Usage

## 1. Run locally
~~~bash
# Make scripts executable
chmod +x scripts/*.sh
chmod +x scripts/*.py

# Setup development environment
./scripts/setup_dev.sh

# Activate virtual environment
source .venv/bin/activate

# Run the full pipeline locally
./scripts/lint.sh
pytest tests/ --junitxml=test-results/junit.xml --cov=src
python scripts/generate_report.py
~~~


## Quick Fix Options:
~~~bash
# Run isort to automatically fix import sorting
isort .

# Then run black to ensure proper formatting
black .

# Verify the fixes
isort --check-only .
black --check .

# Check only (CI mode)
./scripts/lint.sh

# Auto-fix all issues (development mode)
./scripts/lint.sh --fix
~~~
