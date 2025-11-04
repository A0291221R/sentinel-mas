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


## Local Sanity Check:
~~~bash
# Run isort to automatically fix import sorting
uv run isort .
uv run black .
uv run flake8 .
uv run mypy sentinel_mas tests
uv run pytest


## Verify the fixes:
isort --check-only .
black --check .

# Check only (CI mode)
./scripts/lint.sh

# Auto-fix all issues (development mode)
./scripts/lint.sh --fix
~~~


### SonarCube Integration
~~~ bash
## Download SonarCube
cd /d/NUS/Mtech\ IS/Year\ 2\ Sem\ 2/Practice\ Module/Development/sentinel/
curl -L -o sonar-scanner.zip https://binaries.sonarsource.com/Distribution/sonar-scanner-cli/sonar-scanner-cli-5.0.1.3006-windows.zip
unzip sonar-scanner.zip -d tools


## update environment variable
export PATH="$PWD/tools/sonar-scanner-5.0.1.3006-windows/bin:$PATH"

## Verify
sonar-scanner -v
~~~

## Configuration

This project uses separate environment files:

- `.env.sentinel` - Sentinel MAS package configuration
- `.env.api` - API service configuration  
- `.env.shared` - Shared configuration

### Setup

1. Copy example files:
```bash
cp .env.sentinel.example .env.sentinel
cp .env.api.example .env.api
cp .env.shared.example .env.shared
```

2. Edit `.env.sentinel`:
   - Set `OPENAI_API_KEY` with your OpenAI key

3. Edit `.env.api`:
   - Generate `SECRET_KEY`: `openssl rand -hex 32`

4. Run the application:
```bash
python scripts/start_api.py
```

### Environment Files

| File | Purpose | Required Variables |
|------|---------|-------------------|
| `.env.sentinel` | Package config | `OPENAI_API_KEY` |
| `.env.api` | API config | `SECRET_KEY` |
| `.env.shared` | Shared config | None (has defaults) |
```

---

## Migration Steps

1. **Backup your current .env:**
```bash
cp .env .env.backup
```

2. **Create the three new files:**
   - Copy `.env.sentinel` content
   - Copy `.env.api` content
   - Copy `.env.shared` content

3. **Migrate your values:**
   - From old `.env`, copy values to appropriate new files
   - Remove `SENTINEL_` and `API_` prefixes

4. **Update config files:**
   - Replace `sentinel_mas/config.py`
   - Replace `api_service/config.py`

5. **Update .gitignore:**
   - Add the new environment files

6. **Test:**
```bash
python -c "from sentinel_mas.config import Config; print(f'Model: {Config.OPENAI_MODEL}')"
python -c "from api_service.config import get_api_config; print(f'Port: {get_api_config().PORT}')"
```

7. **Start the API:**
```bash
python scripts/start_api.py

---

## Docker Update

**Update `docker/Dockerfile.api`:**

```dockerfile
# Copy environment files
COPY .env.sentinel .env.api .env.shared ./
```

**Update `docker-compose.yml`:**

```yaml
services:
  api:
    volumes:
      - ./.env.sentinel:/app/.env.sentinel
      - ./.env.api:/app/.env.api
      - ./.env.shared:/app/.env.shared
```


### Create Release
~~~bash
# Update version in pyproject.toml
# Edit: version = "0.1.0" → "0.1.1"

# Create release
git tag v0.1.1
git push origin v0.1.1

# Create GitHub release (UI or CLI)
gh release create v0.1.1 --title "Release v0.1.1" --notes "Bug fixes and improvements"
~~~