import json
from typing import Any, Dict

from sentinel_mas.policy_sentinel.policy.security_redactor import SecurityRedactor


class TestSecurityRedactor:

    def test_redactor_loading(self, sample_redactor_policy_file) -> None:
        """Test redactor loads policy correctly"""
        redactor = SecurityRedactor(sample_redactor_policy_file)

        # Test that it can redact without errors
        result = redactor.redact_args({"test": "value"})
        assert result is not None

    def test_sensitive_keys_redaction(self, sample_redactor_policy_file) -> None:
        """Test sensitive keys are redacted"""
        redactor = SecurityRedactor(sample_redactor_policy_file)

        args = {
            "username": "john_doe",
            "password": "secret123",
            "api_token": "token123",
            "resolved_id": "user123",
        }

        redacted = redactor.redact_args(args)

        assert isinstance(redacted, dict)
        assert redacted["username"] == "john_doe"  # Not sensitive
        assert redacted["password"] == "<REDACTED>"
        assert redacted["api_token"] == "<REDACTED>"
        assert redacted["resolved_id"] == "<REDACTED>"

    def test_nested_structure_redaction(self, sample_redactor_policy_file) -> None:
        """Test redaction in nested structures"""
        redactor = SecurityRedactor(sample_redactor_policy_file)

        args = {
            "user": {
                "name": "Alice",
                "credentials": {"password": "secret", "token": "abc123"},
            },
            "metadata": {
                "public_info": "This is public",
                "secret_key": "should_be_redacted",
            },
        }

        redacted = redactor.redact_args(args)

        assert isinstance(redacted, dict)
        assert redacted["user"]["name"] == "Alice"
        assert redacted["user"]["credentials"]["password"] == "<REDACTED>"
        assert redacted["metadata"]["secret_key"] == "<REDACTED>"

    def test_max_depth_respected(self, sample_redactor_policy_file) -> None:
        """Test max depth limit is respected"""
        redactor = SecurityRedactor(sample_redactor_policy_file)

        # Create deeply nested structure
        deep_args = {"level1": {"level2": {"level3": {"level4": {"secret": "value"}}}}}

        redacted = redactor.redact_args(deep_args)

        red_map: Dict[str, Any]
        if isinstance(redacted, str):
            red_map = json.loads(redacted)
        else:
            red_map = redacted

        # Should be truncated at level 4 with max_depth 3
        assert red_map["level1"]["level2"]["level3"]["level4"] == "<...>"

    def test_string_truncation(self, sample_redactor_policy_file) -> None:
        """Test long strings are truncated"""
        redactor = SecurityRedactor(sample_redactor_policy_file)

        long_string = "A" * 200  # Very long string
        args = {"long_data": long_string}

        redacted = redactor.redact_args(args)

        assert isinstance(redacted, Dict)
        assert "...(truncated)" in redacted["long_data"]
        assert len(redacted["long_data"]) < len(long_string)
