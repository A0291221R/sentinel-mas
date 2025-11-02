from pathlib import Path

from sentinel_mas.policy_sentinel.policy.injection_guard import InjectionGuard
from sentinel_mas.policy_sentinel.policy.rbac_loader import RBACPolicy
from sentinel_mas.policy_sentinel.policy.security_redactor import SecurityRedactor

__all__ = ["InjectionGuard", "RBACPolicy", "SecurityRedactor"]

# Get the directory where THIS file lives
_MODULE_DIR = Path(__file__).parent.resolve()
_CONFIG_DIR = _MODULE_DIR / "configs"

# Use absolute paths relative to this module
rbac = RBACPolicy(_CONFIG_DIR / "rbac_policy.yml")
guard = InjectionGuard(_CONFIG_DIR / "injection_policy.yml")
redactor = SecurityRedactor(_CONFIG_DIR / "redactor_policy.yml")
