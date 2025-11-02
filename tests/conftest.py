import sys
from datetime import datetime
from pathlib import Path

import pytest

# # Add the project root to Python path
project_root = Path(__file__).parent.parent
# print(f'project_root: {project_root}')
sys.path.insert(0, str(project_root))


# Test Report with JUnit
def pytest_configure(config):
    """Configure pytest hooks for better JUnit reporting"""
    config.option.xmlpath = (
        f"test-results/junit-{datetime.now().strftime('%Y%m%d-%H%M%S')}.xml"
    )


def pytest_sessionfinish(session, exitstatus):
    """Called after whole test run finished"""
    print(f"\nTest session finished with status: {exitstatus}")


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Add custom properties to JUnit report"""
    outcome = yield
    report = outcome.get_result()

    if report.when == "call":
        # Add custom properties to JUnit XML
        report.user_properties.append(("test_module", item.module.__name__))
        report.user_properties.append(("test_function", item.function.__name__))
