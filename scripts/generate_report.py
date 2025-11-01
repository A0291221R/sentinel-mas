#!/usr/bin/env python3
"""
Generate test report summary from JUnit XML - Python 3.12 compatible
"""
import glob
import json
import os
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Any


def generate_test_report() -> None:
    """Generate human-readable test report from JUnit XML files"""
    junit_files = glob.glob("test-results/junit-*.xml")

    if not junit_files:
        print("❌ No JUnit test results found!")
        return

    total_stats: dict[str, Any] = {
        "tests": 0,
        "failures": 0,
        "errors": 0,
        "skipped": 0,
        "time": 0.0,
        "python_versions": [],
    }

    print("=" * 80)
    print("🐍 PYTHON 3.12 CI/CD - TEST EXECUTION SUMMARY")
    print("=" * 80)

    for junit_file in junit_files:
        try:
            tree = ET.parse(junit_file)
            root = tree.getroot()

            tests = int(root.attrib.get("tests", 0))
            failures = int(root.attrib.get("failures", 0))
            errors = int(root.attrib.get("errors", 0))
            skipped = int(root.attrib.get("skipped", 0))
            time = float(root.attrib.get("time", 0))

            total_stats["tests"] += tests
            total_stats["failures"] += failures
            total_stats["errors"] += errors
            total_stats["skipped"] += skipped
            total_stats["time"] += time

            # Extract Python version from filename
            py_version = (
                os.path.basename(junit_file).replace("junit-", "").replace(".xml", "")
            )
            total_stats["python_versions"].append(py_version)

            status = "✅ PASS" if failures == 0 and errors == 0 else "❌ FAIL"

            print(f"\n📊 Python {py_version}: {status}")
            print(
                f"   Tests: {tests} | Failures: {failures} | Errors: {errors} | \
                Skipped: {skipped} | Time: {time:.2f}s"
            )

            # Show failed tests
            if failures > 0 or errors > 0:
                print("\n   🔴 Failed/Errored Tests:")
                for testcase in root.findall(".//testcase"):
                    failure = testcase.find("failure")
                    error = testcase.find("error")
                    if failure is not None or error is not None:
                        test_name = testcase.attrib.get("name", "Unknown")
                        class_name = testcase.attrib.get("classname", "Unknown")
                        print(f"      - {class_name}.{test_name}")

        except ET.ParseError as e:
            print(f"⚠️  Error parsing {junit_file}: {e}")
            continue

    print("\n" + "=" * 80)
    print("📈 TOTAL SUMMARY")
    print("=" * 80)
    print(f"🧪 Total Tests:    {total_stats['tests']}")
    print(f"🔴 Total Failures: {total_stats['failures']}")
    print(f"🟠 Total Errors:   {total_stats['errors']}")
    print(f"⚪ Total Skipped:  {total_stats['skipped']}")
    print(f"⏱️  Total Time:     {total_stats['time']:.2f}s")
    print(f"🐍 Python Versions: {', '.join(total_stats['python_versions'])}")

    if total_stats["tests"] > 0:
        success_rate = (
            (total_stats["tests"] - total_stats["failures"] - total_stats["errors"])
            / total_stats["tests"]
            * 100
        )
        print(f"✅ Success Rate:   {success_rate:.1f}%")

        if success_rate == 100:
            print("🎉 Excellent! All tests passed!")
        elif success_rate >= 90:
            print("👍 Good! Most tests passed.")
        else:
            print("⚠️  Needs improvement.")
    else:
        success_rate = 0
        print("❌ No tests were executed!")

    # Write detailed report
    with open("test-results/test-summary.md", "w") as f:
        f.write("# Test Execution Summary\n\n")
        f.write(f"- **Total Tests**: {total_stats['tests']}\n")
        f.write(f"- **Failures**: {total_stats['failures']}\n")
        f.write(f"- **Errors**: {total_stats['errors']}\n")
        f.write(f"- **Skipped**: {total_stats['skipped']}\n")
        f.write(f"- **Success Rate**: {success_rate:.1f}%\n")
        f.write(f"- **Total Time**: {total_stats['time']:.2f}s\n")
        f.write(f"- **Python Versions**: {', '.join(total_stats['python_versions'])}\n")
        f.write(f"- **Generated**: {datetime.now().isoformat()}\n")

    # Write JSON report for machine reading
    with open("test-results/test-summary.json", "w") as f:
        json.dump(total_stats, f, indent=2)


if __name__ == "__main__":
    generate_test_report()
