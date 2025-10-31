import pytest
from pathlib import Path
from sentinel_mas.policy_sentinel.policy.rbac_loader import RBACPolicy

class TestRBACPolicy:
    
    def test_rbac_loader_valid_policy(self, sample_rbac_policy_file):
        """Test loading valid RBAC policy"""
        policy = RBACPolicy(sample_rbac_policy_file)
        
        assert policy.version == "1.1"
        assert "operator" in policy.roles
        assert "viewer" in policy.roles

    def test_rbac_is_allowed_success(self, sample_rbac_policy_file):
        """Test successful permission checks"""
        policy = RBACPolicy(sample_rbac_policy_file)
        
        allowed, reason = policy.is_allowed("operator", "TRACKING", "who_entered_zone")
        assert allowed is True
        assert reason == "Allowed"

    def test_rbac_is_allowed_denied_role(self, sample_rbac_policy_file):
        """Test permission denied for unknown role"""
        policy = RBACPolicy(sample_rbac_policy_file)
        
        allowed, reason = policy.is_allowed("unknown_role", "TRACKING", "who_entered_zone")
        assert allowed is False
        assert "Unknown role" in reason

    def test_rbac_is_allowed_denied_route(self, sample_rbac_policy_file):
        """Test permission denied for route"""
        policy = RBACPolicy(sample_rbac_policy_file)
        
        allowed, reason = policy.is_allowed("viewer", "TRACKING", "search_sop")
        assert allowed is False
        assert "Route" in reason

    def test_rbac_is_allowed_denied_tool(self, sample_rbac_policy_file):
        """Test permission denied for tool"""
        policy = RBACPolicy(sample_rbac_policy_file)
        
        allowed, reason = policy.is_allowed("operator", "SOP", "invalid_tool")
        assert allowed is False
        assert "Tool" in reason

    def test_get_allowed_tools(self, sample_rbac_policy_file):
        """Test getting allowed tools for role"""
        policy = RBACPolicy(sample_rbac_policy_file)
        
        tools = policy.get_allowed_tools("operator")
        assert "who_entered_zone" in tools
        assert "send_track" in tools

    def test_get_roles(self, sample_rbac_policy_file):
        """Test getting all roles"""
        policy = RBACPolicy(sample_rbac_policy_file)
        
        roles = policy.get_roles()
        assert "operator" in roles
        assert "viewer" in roles

    def test_describe_role(self, sample_rbac_policy_file):
        """Test role description"""
        policy = RBACPolicy(sample_rbac_policy_file)
        
        description = policy.describe("operator")
        assert "operator" in description
        assert "TRACKING" in description

    def test_assert_allowed_success(self, sample_rbac_policy_file):
        """Test assert_allowed doesn't raise for allowed actions"""
        policy = RBACPolicy(sample_rbac_policy_file)
        
        # Should not raise
        policy.assert_allowed("operator", "TRACKING", "who_entered_zone")

    def test_assert_allowed_raises(self, sample_rbac_policy_file):
        """Test assert_allowed raises for denied actions"""
        policy = RBACPolicy(sample_rbac_policy_file)
        
        with pytest.raises(PermissionError):
            policy.assert_allowed("viewer", "TRACKING", "send_track")