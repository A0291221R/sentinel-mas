# Package only (uses sentinel_mas fixtures)
pytest tests/test_sentinel_mas/ -v

# API only (uses api_service fixtures)
pytest tests/test_api_service/ -v

# Everything (uses appropriate fixtures)
pytest tests/ -v

# By component with coverage
pytest tests/test_sentinel_mas/ --cov=sentinel_mas
pytest tests/test_api_service/ --cov=api_service


tests/conftest.py                    # 🌍 Global (both package + API)
    ↓
    ├── test_sentinel_mas/conftest.py  # 📦 Package-specific
    └── test_api_service/conftest.py   # 🌐 API-specific
```

---

## 📂 **Organized Structure:**
```
tests/
├── conftest.py                      # Shared by ALL tests
│   - setup_test_env()
│   - project_root
│   - test_data_dir
│
├── test_sentinel_mas/               # Package tests
│   ├── conftest.py                  # Package fixtures
│   │   - sentinel_config
│   │   - mock_crew
│   │   - sample_query_state
│   └── test_*.py
│
└── test_api_service/                # API tests
    ├── conftest.py                  # API fixtures
    │   - api_client
    │   - supervisor_token/headers
    │   - admin_token/headers
    │   - user_token/headers
    └── test_*.py


### add Makefile
test-package:
	pytest tests/test_sentinel_mas/ -v

test-api:
	pytest tests/test_api_service/ -v

test-all:
	pytest tests/ -v


# All API tests
pytest tests/test_api_service/ -v

# Specific API test
pytest tests/test_api_service/test_auth.py -v

# Package test with coverage
pytest tests/test_sentinel_mas/ -v --cov=sentinel_mas --cov-report=html

# API tests with coverage
pytest tests/test_api_service/ -v --cov=api_service --cov-report=html

# Run All test cases
pytest tests/ -v --cov=sentinel_mas --cov=api_service --cov-report=html