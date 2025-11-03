"""OpenShift Test Input Validator tool for the MCP Server.

This tool validates user inputs for completeness, detects conflicts, and provides
suggestions for correction before test generation.
"""

from typing import Any, Dict, List, Literal, Optional

from workshop_mcp_server.utils.pylogger import get_python_logger

logger = get_python_logger()

# Known OpenShift components and their common features
OCP_COMPONENTS = {
    "kube-apiserver": ["event-ttl", "admission-plugins", "audit", "encryption", "authentication"],
    "kube-controller-manager": ["node-monitor", "pod-gc", "service-account", "replication"],
    "kube-scheduler": ["priorities", "predicates", "binding", "profiles"],
    "oauth": ["identity-providers", "token-config", "session-management", "rbac"],
    "registry": ["storage", "security", "quotas", "image-pruning"],
    "ingress": ["routes", "certificates", "load-balancing", "dns"],
    "etcd": ["backup", "restore", "encryption", "performance"],
    "monitoring": ["prometheus", "alertmanager", "grafana", "metrics"],
    "logging": ["elasticsearch", "fluentd", "kibana", "log-forwarding"],
    "network": ["ovn-kubernetes", "multus", "network-policy", "egress"],
    "storage": ["persistent-volumes", "storage-classes", "csi", "snapshots"],
    "builds": ["build-config", "image-streams", "source-to-image", "webhooks"],
    "machine-config": ["machine-config-pool", "kernel-args", "kubelet-config"],
    "cluster-autoscaler": ["scaling-policies", "node-groups", "metrics"],
    "pod-security-admission": ["policies", "enforcement", "audit", "warn"],
}

# Common API versions
COMMON_API_VERSIONS = [
    "v1",
    "apps/v1",
    "batch/v1",
    "networking.k8s.io/v1",
    "rbac.authorization.k8s.io/v1",
    "config.openshift.io/v1",
    "operator.openshift.io/v1",
    "route.openshift.io/v1",
    "image.openshift.io/v1",
    "build.openshift.io/v1",
]


def validate_ocp_test_input(
    feature: str,
    component: str,
    scenario: str,
    api_version: Optional[str] = None,
    namespace: Optional[str] = None,
    permissions: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Validate user-provided test input for completeness and correctness.

    TOOL_NAME=validate_ocp_test_input
    DISPLAY_NAME=OpenShift Test Input Validator
    USECASE=Validate test inputs for completeness, detect conflicts, and provide suggestions for improvement
    INSTRUCTIONS=1. Provide test details (feature, component, scenario), 2. Optionally include API version and namespace, 3. Receive validation results with suggestions
    INPUT_DESCRIPTION=feature (str): Feature to test, component (str): OCP component name, scenario (str): Test scenario description, api_version (str, optional): K8s API version, namespace (str, optional): Target namespace, permissions (list, optional): Required permissions
    OUTPUT_DESCRIPTION=Dictionary with validation status, issues found, warnings, suggestions, and corrected values
    EXAMPLES=validate_ocp_test_input("Event TTL", "kube-apiserver", "Verify eventTTLMinutes"), validate_ocp_test_input("Pod Security", "pod-security-admission", "Test restricted policy")
    PREREQUISITES=None
    RELATED_TOOLS=generate_ocp_test_case, generate_ocp_automation_code

    This tool performs comprehensive validation including:
    - Component name verification
    - Feature compatibility checking
    - API version validation
    - Namespace naming validation
    - Permission requirements checking
    - Conflict detection

    Args:
        feature: Feature or capability being tested
        component: OpenShift component name
        scenario: Test scenario description
        api_version: Kubernetes/OpenShift API version (optional)
        namespace: Target namespace (optional)
        permissions: List of required permissions (optional)

    Returns:
        Dictionary containing validation results, issues, and suggestions

    Raises:
        ValueError: If critical validation failures occur
    """
    try:
        validation_results = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "suggestions": [],
            "corrected_values": {},
        }

        # Validate required fields
        if not feature or not feature.strip():
            validation_results["errors"].append("Feature is required and cannot be empty")
            validation_results["valid"] = False

        if not component or not component.strip():
            validation_results["errors"].append("Component is required and cannot be empty")
            validation_results["valid"] = False

        if not scenario or not scenario.strip():
            validation_results["errors"].append("Scenario is required and cannot be empty")
            validation_results["valid"] = False

        # Validate component
        if component:
            component_lower = component.lower().replace("_", "-")
            if component_lower not in OCP_COMPONENTS:
                similar = _find_similar_component(component_lower)
                if similar:
                    validation_results["warnings"].append(f"Component '{component}' not recognized. Did you mean '{similar}'?")
                    validation_results["suggestions"].append(f"Consider using '{similar}' as the component name")
                    validation_results["corrected_values"]["component"] = similar
                else:
                    validation_results["warnings"].append(
                        f"Component '{component}' not in known components list. This may still be valid for custom components."
                    )
                    validation_results["suggestions"].append(f"Known components: {', '.join(list(OCP_COMPONENTS.keys())[:10])}")
            else:
                # Check if feature is relevant to component
                component_features = OCP_COMPONENTS[component_lower]
                feature_match = _find_feature_match(feature, component_features)
                if not feature_match:
                    validation_results["suggestions"].append(
                        f"Common features for {component}: {', '.join(component_features[:5])}"
                    )

        # Validate API version
        if api_version:
            if api_version not in COMMON_API_VERSIONS:
                validation_results["warnings"].append(
                    f"API version '{api_version}' is not in common API versions list. Verify this is correct."
                )
                validation_results["suggestions"].append(f"Common API versions: {', '.join(COMMON_API_VERSIONS[:5])}")

        # Validate namespace
        if namespace:
            namespace_validation = _validate_namespace(namespace)
            if not namespace_validation["valid"]:
                validation_results["errors"].append(namespace_validation["error"])
                validation_results["valid"] = False
            if namespace_validation.get("warning"):
                validation_results["warnings"].append(namespace_validation["warning"])

        # Validate permissions
        if permissions:
            permission_validation = _validate_permissions(permissions)
            validation_results["warnings"].extend(permission_validation.get("warnings", []))
            validation_results["suggestions"].extend(permission_validation.get("suggestions", []))

        # Check for common issues
        common_issues = _check_common_issues(feature, component, scenario)
        validation_results["suggestions"].extend(common_issues)

        # Generate recommendations
        recommendations = _generate_recommendations(feature, component, scenario, api_version, namespace)
        validation_results["recommendations"] = recommendations

        logger.info(f"Validation completed: {'VALID' if validation_results['valid'] else 'INVALID'}")

        return {
            "status": "success",
            "validation": validation_results,
            "summary": _generate_validation_summary(validation_results),
            "message": "Input validation completed",
        }

    except Exception as e:
        logger.error(f"Error validating test input: {e}")
        return {
            "status": "error",
            "error": str(e),
            "message": "Failed to validate test input",
        }


def _find_similar_component(component: str) -> Optional[str]:
    """Find similar component name using fuzzy matching."""
    component = component.lower().replace("_", "-")

    # Exact match
    if component in OCP_COMPONENTS:
        return component

    # Partial match
    for known_component in OCP_COMPONENTS:
        if component in known_component or known_component in component:
            return known_component

    # Check for common abbreviations
    abbreviations = {
        "api-server": "kube-apiserver",
        "apiserver": "kube-apiserver",
        "controller": "kube-controller-manager",
        "scheduler": "kube-scheduler",
        "auth": "oauth",
        "authentication": "oauth",
        "reg": "registry",
        "router": "ingress",
        "log": "logging",
        "net": "network",
        "mco": "machine-config",
    }

    for abbr, full_name in abbreviations.items():
        if abbr in component:
            return full_name

    return None


def _find_feature_match(feature: str, component_features: List[str]) -> bool:
    """Check if feature matches known features for component."""
    feature_lower = feature.lower()

    for known_feature in component_features:
        if known_feature in feature_lower or feature_lower in known_feature:
            return True

    return False


def _validate_namespace(namespace: str) -> Dict[str, Any]:
    """Validate namespace naming conventions."""
    result = {"valid": True}

    # DNS-1123 label validation (RFC 1123)
    import re

    # Namespace must be lowercase alphanumeric with hyphens
    pattern = r"^[a-z0-9]([-a-z0-9]*[a-z0-9])?$"

    if not re.match(pattern, namespace):
        result["valid"] = False
        result["error"] = f"Namespace '{namespace}' must match DNS-1123: lowercase alphanumeric with hyphens"
        return result

    # Length check
    if len(namespace) > 63:
        result["valid"] = False
        result["error"] = f"Namespace '{namespace}' exceeds maximum length of 63 characters"
        return result

    # Reserved namespaces warning
    reserved_prefixes = ["kube-", "openshift-", "default", "kubernetes-"]
    for prefix in reserved_prefixes:
        if namespace.startswith(prefix):
            result["warning"] = (
                f"Namespace '{namespace}' uses reserved prefix '{prefix}'. Ensure you have proper permissions."
            )
            break

    return result


def _validate_permissions(permissions: List[str]) -> Dict[str, Any]:
    """Validate permission requirements."""
    result = {"warnings": [], "suggestions": []}

    known_permissions = [
        "get",
        "list",
        "watch",
        "create",
        "update",
        "patch",
        "delete",
        "deletecollection",
        "cluster-admin",
        "admin",
        "edit",
        "view",
    ]

    for perm in permissions:
        if perm not in known_permissions:
            result["warnings"].append(f"Permission '{perm}' is not a standard RBAC permission")

    if "cluster-admin" in permissions:
        result["suggestions"].append(
            "cluster-admin role grants full cluster access. Consider if a more restricted role would be appropriate."
        )

    return result


def _check_common_issues(feature: str, component: str, scenario: str) -> List[str]:
    """Check for common issues in test definitions."""
    issues = []

    # Check for vague descriptions
    vague_terms = ["test", "verify", "check", "validate"]
    if all(term not in scenario.lower() for term in vague_terms):
        issues.append("Scenario should include action verbs like 'verify', 'test', 'validate', or 'check'")

    # Check scenario length
    if len(scenario) < 10:
        issues.append("Scenario description is very short. Consider adding more details about what is being tested.")

    if len(scenario) > 200:
        issues.append("Scenario description is very long. Consider breaking into multiple test scenarios.")

    # Check for hardcoded values in scenario
    if "namespace" in scenario.lower() and "test-" in scenario.lower():
        issues.append("Avoid hardcoding namespace names in scenario. Use parameterized namespaces instead.")

    return issues


def _generate_recommendations(
    feature: str, component: str, scenario: str, api_version: Optional[str], namespace: Optional[str]
) -> List[str]:
    """Generate recommendations for test improvement."""
    recommendations = []

    # API version recommendation
    if not api_version:
        recommendations.append("Consider specifying an API version for better test accuracy")

    # Namespace recommendation
    if not namespace:
        recommendations.append("Consider specifying a namespace for test isolation")
    elif not namespace.startswith("test-") and not namespace.startswith("e2e-"):
        recommendations.append("Consider using 'test-' or 'e2e-' prefix for test namespaces")

    # Component-specific recommendations
    component_lower = component.lower().replace("_", "-")
    if component_lower == "kube-apiserver":
        recommendations.append("For kube-apiserver tests, ensure you verify configuration in both static pods and cluster operator")
    elif component_lower == "etcd":
        recommendations.append("For etcd tests, consider testing backup/restore scenarios and encryption at rest")
    elif component_lower == "oauth":
        recommendations.append("For oauth tests, ensure you test with multiple identity providers if applicable")

    # Feature-specific recommendations
    if "event" in feature.lower() or "ttl" in feature.lower():
        recommendations.append("For event-related tests, verify both event creation and retention/expiration")

    if "security" in feature.lower() or "policy" in feature.lower():
        recommendations.append("For security tests, include both positive (allowed) and negative (denied) test cases")

    return recommendations


def _generate_validation_summary(validation_results: Dict[str, Any]) -> str:
    """Generate human-readable validation summary."""
    errors = len(validation_results.get("errors", []))
    warnings = len(validation_results.get("warnings", []))
    suggestions = len(validation_results.get("suggestions", []))

    if validation_results["valid"]:
        if warnings == 0 and suggestions == 0:
            return "✅ All inputs are valid. Ready to generate test case."
        else:
            return f"⚠️ Inputs are valid but have {warnings} warning(s) and {suggestions} suggestion(s) for improvement."
    else:
        return f"❌ Validation failed with {errors} error(s). Please fix before proceeding."


def suggest_test_improvements(
    test_case_content: str,
    test_format: Literal["gherkin", "yaml", "go"] = "gherkin",
) -> Dict[str, Any]:
    """Analyze generated test case and suggest improvements.

    TOOL_NAME=suggest_test_improvements
    DISPLAY_NAME=Test Case Improvement Suggester
    USECASE=Analyze generated test cases and provide suggestions for quality, coverage, and best practices
    INSTRUCTIONS=1. Provide generated test case content and format, 2. Receive detailed improvement suggestions
    INPUT_DESCRIPTION=test_case_content (str): Generated test case code/content, test_format (str): Format of test (gherkin/yaml/go)
    OUTPUT_DESCRIPTION=Dictionary with improvement suggestions, best practice violations, coverage gaps, and enhanced test recommendations
    EXAMPLES=suggest_test_improvements(gherkin_test, "gherkin"), suggest_test_improvements(go_test_code, "go")
    PREREQUISITES=Valid test case content from generate_ocp_test_case
    RELATED_TOOLS=generate_ocp_test_case, validate_ocp_test_input

    Args:
        test_case_content: Generated test case content
        test_format: Format of the test case

    Returns:
        Dictionary containing improvement suggestions and recommendations
    """
    try:
        suggestions = {
            "best_practices": [],
            "coverage_gaps": [],
            "improvements": [],
            "anti_patterns": [],
        }

        content_lower = test_case_content.lower()

        # Check for best practices
        if "cleanup" not in content_lower and "aftereach" not in content_lower:
            suggestions["best_practices"].append("Add cleanup logic to remove test resources after execution")

        if "timeout" not in content_lower:
            suggestions["best_practices"].append("Consider adding timeout constraints to prevent hanging tests")

        if test_format == "go":
            if "gomega" not in content_lower:
                suggestions["best_practices"].append("Use Gomega assertions for better error messages")

            if "context.context" not in content_lower and "ctx context.context" not in content_lower:
                suggestions["best_practices"].append("Use context.Context for proper cancellation and timeout handling")

        # Check for coverage gaps
        if "error" not in content_lower and "fail" not in content_lower:
            suggestions["coverage_gaps"].append("Add negative test cases to verify error handling")

        if "log" not in content_lower:
            suggestions["coverage_gaps"].append("Include log verification to catch runtime errors")

        if "persist" not in content_lower and "restart" not in content_lower:
            suggestions["coverage_gaps"].append("Test configuration persistence across pod/component restarts")

        # Check for anti-patterns
        if "sleep" in content_lower and "time.sleep" in content_lower:
            suggestions["anti_patterns"].append("Avoid fixed sleep() calls. Use proper wait conditions with timeouts instead")

        if "hardcoded" in content_lower or any(
            x in content_lower for x in ['"default"', "'default'", '"test"', "'test'"]
        ):
            suggestions["anti_patterns"].append("Avoid hardcoded namespaces. Use dynamic namespace creation")

        # General improvements
        if test_format == "gherkin":
            if "background:" not in content_lower:
                suggestions["improvements"].append("Use Background section for common setup steps")

        if test_format == "yaml":
            if "preconditions" not in content_lower:
                suggestions["improvements"].append("Add preconditions to validate test environment before execution")

        return {
            "status": "success",
            "suggestions": suggestions,
            "total_suggestions": sum(len(v) for v in suggestions.values()),
            "message": "Test improvement analysis completed",
        }

    except Exception as e:
        logger.error(f"Error suggesting improvements: {e}")
        return {
            "status": "error",
            "error": str(e),
            "message": "Failed to analyze test case",
        }
