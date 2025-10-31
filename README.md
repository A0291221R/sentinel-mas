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

