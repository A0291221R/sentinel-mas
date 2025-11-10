# GitHub Actions CI/CD Pipeline Explanation

## Overview

Your project uses a **4-stage CI/CD pipeline** that automates everything from code quality checks to Docker image deployment. The workflows are designed to run sequentially, with each stage depending on the successful completion of the previous one.

---

## Pipeline Stages

### **STAGE 1: Continuous Integration (ci.yaml)**

**Purpose:** Ensure code quality and run all tests before any deployment

**Triggers:**
- Push to `main` or `develop` branches
- Pull requests to `main`
- Manual trigger
- Nightly scheduled run (2 AM UTC)

**Jobs:**

1. **Code Quality & Linting**
   - Runs Black (code formatting)
   - Runs isort (import sorting)
   - Runs flake8 (style guide)
   - Runs mypy (type checking)
   - Scope: `sentinel_mas` and `api_service` only
   - Excludes: `sentinel_central` and `chatbot_ui`

2. **Unit & Integration Tests** (Parallel execution)
   - Three test suites run in parallel:
     - Unit tests for `sentinel_mas`
     - Integration tests for `sentinel_mas`
     - API service tests
   - Generates coverage reports
   - Only runs if code quality passes

3. **Security Scan**
   - Runs Bandit (security linter)
   - Runs Safety (dependency vulnerability check)
   - Runs in parallel with tests

4. **SonarQube Analysis**
   - Code quality gate check
   - Analyzes coverage reports
   - Posts results to PRs
   - Requires tests to complete first

5. **Test Report Aggregation**
   - Consolidates all test results
   - Uploads to Codecov
   - Creates unified reports

6. **CI Status Check**
   - Final gate that checks all jobs
   - Must pass for pipeline to continue
   - Required for branch protection

**Outputs:**
- Test artifacts
- Coverage reports
- Security scan results

---

### **STAGE 2: Package Building & Publishing (package-build.yaml)**

**Purpose:** Build and publish the Python package to PyPI

**Triggers:**
- Push to `main` (after Stage 1 completes)
- Release created/published
- Manual trigger

**Jobs:**

1. **Version Management**
   - Extracts version from `pyproject.toml`
   - Validates version format
   - Determines if this is a release or development build
   - Sets publish strategy

2. **Build Python Package**
   - Creates wheel (`.whl`) and source distribution (`.tar.gz`)
   - Verifies package structure
   - Generates build metadata
   - Runs twine validation
   - Creates SHA256 checksums

3. **Test Package**
   - Installs the built package in a clean environment
   - Runs smoke tests
   - Verifies all imports work
   - Tests package uninstall

4. **Publish Strategy** (Conditional)
   - **If Release:** Publishes to PyPI (production)
   - **If Development:** Publishes to Test PyPI (testing)

5. **Generate Release Notes** (Release only)
   - Creates changelog from git history
   - Includes package details and checksums
   - Uploads as artifact

**Outputs:**
- Python package artifacts
- PyPI package: `sentinel-mas`
- Release notes

---

### **STAGE 3: Build API Docker Image (docker-api.yaml)**

**Purpose:** Build and deploy the API service Docker image

**Triggers:**
- After Stage 2 completes successfully
- Release published
- Manual trigger (with optional version parameter)

**Jobs:**

**Build & Push API Image**
   - Checks out code and verifies required files
   - Gets `sentinel-mas` version from `pyproject.toml`
   - Configures AWS credentials
   - Logs into Amazon ECR
   - Builds Docker image with build args
   - Tests image locally:
     - Runs container with test environment variables
     - Checks `/health` endpoint
     - Verifies service starts correctly
   - Pushes three tags to ECR:
     - Version tag (e.g., `0.1.0`)
     - `latest` tag
     - Git SHA tag (for traceability)

**Docker Image Details:**
- Repository: `sentinel-mas-api`
- Base: Uses `api_service/Dockerfile`
- Port: 8000
- Health check: `/health`

**Outputs:**
- ECR Image: `sentinel-mas-api:version`
- ECR Image: `sentinel-mas-api:latest`
- ECR Image: `sentinel-mas-api:sha`

---

### **STAGE 4: Build UI Docker Image (docker-ui.yaml)**

**Purpose:** Build and deploy the UI service Docker image

**Triggers:**
- After Stage 3 completes successfully
- Push to `main` with UI changes
- Release published
- Manual trigger

**Jobs:**

**Build & Push UI Image**
   - Checks out and verifies `chatbot_ui` files
   - Gets version from `pyproject.toml`
   - Configures AWS & ECR
   - Builds Docker image
   - Tests image locally:
     - Runs container on port 8080
     - Sets API URLs via environment variables
     - Checks `/health` endpoint
   - Pushes three tags to ECR

**Docker Image Details:**
- Repository: `sentinel-mas-ui`
- Base: Uses `chatbot_ui/Dockerfile` (nginx-based)
- Port: 80 (mapped from 8080 in tests)
- Static files: HTML/CSS/JS

**Outputs:**
- ECR Image: `sentinel-mas-ui:version`
- ECR Image: `sentinel-mas-ui:latest`
- ECR Image: `sentinel-mas-ui:sha`

---

### **STAGE 4b: Build Sentinel Central Docker Image (docker-central.yaml)**

**Purpose:** Build and deploy the Sentinel Central tracking service

**Triggers:**
- After Stage 3 completes successfully
- Push to `main` with `sentinel_central` changes
- Release published
- Manual trigger

**Jobs:**

**Build & Push Central Image**
   - Verifies `sentinel_central` structure and files
   - Gets version from `pyproject.toml`
   - Configures AWS & ECR
   - Builds Docker image
   - Tests image locally:
     - Runs with test database URL
     - Checks `/healthz` and `/readyz` endpoints
   - Pushes three tags to ECR

**Docker Image Details:**
- Repository: `sentinel-mas-central`
- Base: Uses `sentinel_central/Dockerfile`
- Port: 8100
- Health checks: `/healthz`, `/readyz`

**Outputs:**
- ECR Image: `sentinel-mas-central:version`
- ECR Image: `sentinel-mas-central:latest`
- ECR Image: `sentinel-mas-central:sha`

---

## Workflow Sequence

```
1. Code Push/PR → Stage 1 (CI) runs
                    ↓
2. If Stage 1 passes on main → Stage 2 (Package Build) runs
                                  ↓
3. If Stage 2 completes → Stage 3 (API Docker) runs
                             ↓
4. If Stage 3 completes → Stage 4 (UI Docker) + Stage 4b (Central Docker) run in parallel
```

---

## Key Features

### **Parallel Execution**
- Test suites run in parallel (unit, integration, api)
- UI and Central Docker builds run in parallel
- Reduces total pipeline time

### **Caching Strategy**
- UV package manager caching
- Virtual environment caching
- Docker layer caching (implicit in ECR)

### **Quality Gates**
- Code must pass linting before tests run
- Tests must pass before package builds
- Package must pass validation before publishing
- Docker images must pass health checks before pushing

### **Versioning**
- Single source of truth: `pyproject.toml`
- All artifacts (package, Docker images) use the same version
- Git SHA tagging for traceability

### **Security**
- AWS credentials via GitHub secrets
- ECR trusted publishing
- PyPI trusted publishing (no API keys needed)
- Security scanning with Bandit and Safety

### **Testing at Every Stage**
- Linting in Stage 1
- Unit/integration tests in Stage 1
- Package installation test in Stage 2
- Docker container health checks in Stages 3, 4, 4b

---

## Deployment Targets

### **Development Builds** (non-release)
- Python package → Test PyPI
- Docker images → ECR with version tag

### **Release Builds**
- Python package → Production PyPI
- Docker images → ECR with version, latest, and SHA tags
- Release notes generated

---

## Environment Variables

### **CI Pipeline**
- `PYTHON_VERSION`: "3.12"
- `CHECK_PATHS`: "sentinel_mas api_service"

### **Package Build**
- `PACKAGE_NAME`: "sentinel-mas"

### **Docker Builds**
- `AWS_REGION`: "us-east-1"
- `ECR_REPOSITORY`: Different for each service

---

## Artifacts & Outputs

1. **GitHub Artifacts:**
   - Test results (30 days)
   - Coverage reports (30 days)
   - Python packages (90 days)
   - Release notes (90 days)

2. **PyPI:**
   - Published Python package
   - Available via `pip install sentinel-mas`

3. **Amazon ECR:**
   - Three Docker images with multiple tags each
   - Ready for deployment to ECS/EKS/EC2

---

## Best Practices Implemented

✅ **Sequential dependencies** - Each stage builds on the previous
✅ **Fail fast** - Stops at first failure
✅ **Parallel where possible** - Tests and Docker builds
✅ **Comprehensive testing** - Unit, integration, security, smoke tests
✅ **Artifact retention** - All builds are preserved
✅ **Traceability** - Git SHA tagging on all outputs
✅ **Documentation** - Step summaries and release notes
✅ **Manual controls** - workflow_dispatch on all workflows

---

## How to Use

### **For Development:**
1. Push code to `develop` or create PR → Stage 1 runs
2. Merge to `main` → Full pipeline runs
3. Check artifacts in GitHub Actions

### **For Release:**
1. Update version in `pyproject.toml`
2. Create GitHub release
3. All stages run automatically
4. Package published to PyPI
5. Docker images tagged with version and latest

### **For Hotfixes:**
1. Use `workflow_dispatch` to manually trigger specific stages
2. Can specify version for API Docker build
3. Useful for rebuilding without full pipeline
