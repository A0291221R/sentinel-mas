from sentinel_mas.policy_sentinel.policy.injection_guard import InjectionGuard
from sentinel_mas.policy_sentinel.policy.rbac_loader import RBACPolicy
from sentinel_mas.policy_sentinel.policy.security_redactor import SecurityRedactor

rbac = RBACPolicy("sentinel_mas/policy_sentinel/configs/rbac_policy.yml")
guard = InjectionGuard("sentinel_mas/policy_sentinel/configs/injection_policy.yml")
redactor = SecurityRedactor("sentinel_mas/policy_sentinel/configs/redactor_policy.yml")