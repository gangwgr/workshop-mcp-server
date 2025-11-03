"""OpenShift Test Case Generator tool for the MCP Server.

This tool generates comprehensive test cases for OpenShift in multiple formats:
- Gherkin (Behavior-Driven Development)
- YAML (declarative test definitions)
- Go/Ginkgo (executable test code)
"""

from typing import Any, Dict, Literal, Optional

from workshop_mcp_server.utils.pylogger import get_python_logger

logger = get_python_logger()


def generate_ocp_test_case(
    feature: str,
    component: str,
    scenario: str,
    test_format: Literal["gherkin", "yaml", "go"] = "gherkin",
    api_version: Optional[str] = None,
    namespace: Optional[str] = None,
    description: Optional[str] = None,
) -> Dict[str, Any]:
    """Generate OpenShift test cases in various formats.

    TOOL_NAME=generate_ocp_test_case
    DISPLAY_NAME=OpenShift Test Case Generator
    USECASE=Generate comprehensive OCP test cases in Gherkin, YAML, or Go/Ginkgo format
    INSTRUCTIONS=1. Provide feature, component, and scenario details, 2. Select output format, 3. Receive generated test case
    INPUT_DESCRIPTION=feature (str): Feature being tested (e.g., "kube-apiserver event retention"), component (str): OCP component (e.g., "kube-apiserver"), scenario (str): Test scenario description, test_format (str): Output format (gherkin/yaml/go), api_version (str, optional): API version, namespace (str, optional): K8s namespace, description (str, optional): Additional test description
    OUTPUT_DESCRIPTION=Dictionary with status, generated test case content, format, and metadata
    EXAMPLES=generate_ocp_test_case("Event TTL Configuration", "kube-apiserver", "Verify eventTTLMinutes setting", "gherkin"), generate_ocp_test_case("Pod Security", "pod-security-admission", "Test restricted policy enforcement", "go")
    PREREQUISITES=Valid OpenShift feature and component names
    RELATED_TOOLS=generate_ocp_automation_code, validate_ocp_test_input

    This tool generates production-ready test cases following Red Hat's OCP testing guidelines.

    Args:
        feature: Feature or capability being tested
        component: OpenShift component (e.g., kube-apiserver, oauth, registry)
        scenario: Specific test scenario description
        test_format: Output format - "gherkin", "yaml", or "go"
        api_version: Kubernetes API version (optional)
        namespace: Target namespace for test (optional, defaults to generated temp namespace)
        description: Additional description or context (optional)

    Returns:
        Dictionary containing the generated test case with metadata

    Raises:
        ValueError: If inputs are invalid or incomplete
    """
    try:
        # Validate inputs
        if not feature or not component or not scenario:
            raise ValueError("feature, component, and scenario are required fields")

        if test_format not in ["gherkin", "yaml", "go"]:
            raise ValueError(f"Invalid format: {test_format}. Must be gherkin, yaml, or go")

        logger.info(f"Generating {test_format} test case for {component}/{feature}")

        # Try LLM-powered test generation first
        try:
            from workshop_mcp_server.src.tools.llm_provider import generate_test_case, is_available
            if is_available():
                llm_result = generate_test_case(
                    feature=feature, component=component, scenario=scenario,
                    test_format=test_format, description=description or ""
                )
                if llm_result:
                    logger.info("LLM-powered test case generation completed")
                    return {
                        "status": "success",
                        "format": test_format,
                        "feature": feature,
                        "component": component,
                        "scenario": scenario,
                        "test_case": llm_result,
                        "mode": "llm",
                        "metadata": {
                            "api_version": api_version or "N/A",
                            "namespace": namespace or "auto-generated",
                            "description": description or "N/A",
                        },
                        "message": f"AI-generated {test_format} test case for {feature} (llama3)",
                    }
        except Exception as llm_err:
            logger.warning(f"LLM test gen unavailable, falling back to templates: {llm_err}")

        # Generate test case based on format (template fallback)
        if test_format == "gherkin":
            test_content = _generate_gherkin(feature, component, scenario, description, api_version, namespace)
        elif test_format == "yaml":
            test_content = _generate_yaml(feature, component, scenario, description, api_version, namespace)
        else:  # go
            test_content = _generate_go(feature, component, scenario, description, api_version, namespace)

        return {
            "status": "success",
            "format": test_format,
            "feature": feature,
            "component": component,
            "scenario": scenario,
            "test_case": test_content,
            "metadata": {
                "api_version": api_version or "N/A",
                "namespace": namespace or "auto-generated",
                "description": description or "N/A",
            },
            "message": f"Successfully generated {test_format} test case for {feature}",
        }

    except Exception as e:
        logger.error(f"Error generating test case: {e}")
        return {
            "status": "error",
            "error": str(e),
            "message": "Failed to generate test case",
        }


def _generate_gherkin(
    feature: str, component: str, scenario: str, description: Optional[str], api_version: Optional[str], namespace: Optional[str]
) -> str:
    """Generate Gherkin format test case."""
    namespace_str = namespace or "${NAMESPACE}"
    api_ver_str = api_version or "v1"
    desc_str = description or f"Test {component} {feature} functionality"

    gherkin = f"""Feature: {feature}
  As an OpenShift administrator
  I want to test {component} {feature.lower()}
  So that I can ensure proper functionality

  Background:
    Given an OpenShift cluster is available
    And I have cluster-admin privileges
    And namespace "{namespace_str}" is created or available

  Scenario: {scenario}
    {desc_str}

    Given the {component} component is deployed
    And the API version is "{api_ver_str}"
    When I apply the test configuration
    Then the configuration should be accepted
    And I verify the expected behavior
    And logs show no errors
    And the system remains stable

  Scenario: Verify configuration persistence
    Given the test configuration is applied
    When I restart the {component} pods
    Then the configuration should persist
    And the feature should remain functional

  Scenario: Cleanup and validation
    Given all test configurations are applied
    When I remove the test configuration
    Then the system should return to default state
    And no residual configuration remains
"""
    return gherkin


def _generate_yaml(
    feature: str, component: str, scenario: str, description: Optional[str], api_version: Optional[str], namespace: Optional[str]
) -> str:
    """Generate YAML format test definition."""
    namespace_str = namespace or "test-${RANDOM_ID}"
    api_ver_str = api_version or "v1"
    desc_str = description or f"Test {component} {feature} functionality"

    yaml_content = f"""apiVersion: test.openshift.io/v1
kind: TestCase
metadata:
  name: {component.lower().replace('_', '-')}-{feature.lower().replace(' ', '-')}
  labels:
    component: {component}
    feature: {feature.lower().replace(' ', '-')}
    test-type: functional
spec:
  description: |
    {desc_str}
    Scenario: {scenario}

  component: {component}
  apiVersion: {api_ver_str}
  namespace: {namespace_str}

  preconditions:
    - description: OpenShift cluster is accessible
      validation: oc cluster-info
    - description: User has cluster-admin role
      validation: oc auth can-i '*' '*' --all-namespaces
    - description: Target namespace exists or can be created
      validation: oc get namespace {namespace_str} || oc create namespace {namespace_str}

  testSteps:
    - name: setup
      description: Prepare test environment
      actions:
        - type: create-namespace
          namespace: {namespace_str}
        - type: verify-component
          component: {component}

    - name: execute-test
      description: {scenario}
      actions:
        - type: apply-configuration
          resource: test-config.yaml
        - type: wait-for-ready
          timeout: 300s
        - type: verify-behavior
          expected: configuration-applied

    - name: validate-results
      description: Verify test outcomes
      validations:
        - type: check-logs
          component: {component}
          expected: no-errors
        - type: verify-metrics
          metric: configuration_applied
          expected: true

    - name: cleanup
      description: Remove test resources
      actions:
        - type: delete-configuration
        - type: verify-cleanup
        - type: delete-namespace
          namespace: {namespace_str}
          ignore-not-found: true

  expectedResults:
    - {scenario} completes successfully
    - No errors in component logs
    - Configuration persists across restarts
    - System remains stable

  timeout: 600s
  retries: 1
"""
    return yaml_content


def _generate_go(
    feature: str, component: str, scenario: str, description: Optional[str], api_version: Optional[str], namespace: Optional[str]
) -> str:
    """Generate Go/Ginkgo format test code."""
    desc_str = description or f"Test {component} {feature} functionality"
    package_name = component.lower().replace("-", "_")
    test_name = feature.replace(" ", "").replace("-", "")

    go_content = f'''package {package_name}_test

import (
\t"context"
\t"fmt"
\t"time"

\t. "github.com/onsi/ginkgo/v2"
\t. "github.com/onsi/gomega"

\tcorev1 "k8s.io/api/core/v1"
\tmetav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
\t"k8s.io/client-go/kubernetes"

\te2e "github.com/openshift/origin/test/extended/util"
\texutil "github.com/openshift/origin/test/extended/util"
)

var _ = Describe("[{component}] {feature}", func() {{
\tdefer GinkgoRecover()

\tvar (
\t\toc           *exutil.CLI
\t\tclientset    kubernetes.Interface
\t\ttestNs       string
\t\tcleanupFuncs []func() error
\t)

\tBeforeEach(func() {{
\t\t// Initialize test context
\t\toc = exutil.NewCLI("{component.lower()}-test")
\t\tclientset = oc.AdminKubeClient()
\t\t
\t\t// Create unique test namespace
\t\ttestNs = fmt.Sprintf("e2e-{component.lower()}-%d", time.Now().Unix())
\t\tns := &corev1.Namespace{{
\t\t\tObjectMeta: metav1.ObjectMeta{{
\t\t\t\tName: testNs,
\t\t\t}},
\t\t}}
\t\t_, err := clientset.CoreV1().Namespaces().Create(context.TODO(), ns, metav1.CreateOptions{{}})
\t\tExpect(err).NotTo(HaveOccurred(), "Failed to create test namespace")
\t\t
\t\tcleanupFuncs = []func() error{{}}
\t}})

\tAfterEach(func() {{
\t\t// Execute cleanup functions
\t\tfor _, cleanup := range cleanupFuncs {{
\t\t\tif err := cleanup(); err != nil {{
\t\t\t\tGinkgoLogr.Error(err, "Cleanup function failed")
\t\t\t}}
\t\t}}
\t\t
\t\t// Delete test namespace
\t\terr := clientset.CoreV1().Namespaces().Delete(context.TODO(), testNs, metav1.DeleteOptions{{}})
\t\tif err != nil {{
\t\t\tGinkgoLogr.Error(err, "Failed to delete test namespace", "namespace", testNs)
\t\t}}
\t}})

\tIt("{scenario}", func(ctx context.Context) {{
\t\t// Test Description: {desc_str}
\t\t
\t\t// Step 1: Verify component is running
\t\tBy("Verifying {component} component is deployed and healthy")
\t\tpods, err := clientset.CoreV1().Pods("openshift-{component.lower()}").List(ctx, metav1.ListOptions{{
\t\t\tLabelSelector: "app={component.lower()}",
\t\t}})
\t\tExpect(err).NotTo(HaveOccurred())
\t\tExpect(pods.Items).NotTo(BeEmpty(), "{component} pods should be running")
\t\t
\t\t// Step 2: Apply test configuration
\t\tBy("Applying test configuration")
\t\t// TODO: Implement your test configuration here
\t\t// Example: Update ConfigMap, modify operator config, etc.
\t\t
\t\t// Step 3: Wait for configuration to be applied
\t\tBy("Waiting for configuration to be applied")
\t\ttime.Sleep(10 * time.Second) // Replace with proper wait condition
\t\t
\t\t// Step 4: Verify expected behavior
\t\tBy("Verifying expected behavior")
\t\t// TODO: Implement verification logic
\t\t// Example: Check API responses, verify metrics, inspect resources
\t\t
\t\t// Step 5: Verify logs contain no errors
\t\tBy("Checking {component} logs for errors")
\t\tlogs := oc.Logs().ForPod("{component.lower()}")
\t\tExpect(logs).NotTo(ContainSubstring("ERROR"))
\t\tExpect(logs).NotTo(ContainSubstring("FATAL"))
\t\t
\t\t// Step 6: Verify persistence (restart component)
\t\tBy("Verifying configuration persists after pod restart")
\t\t// TODO: Implement restart and verification
\t\t
\t\tGinkgoLogr.Info("Test completed successfully", "scenario", "{scenario}")
\t}})

\tIt("should cleanup resources properly", func(ctx context.Context) {{
\t\tBy("Removing test configuration")
\t\t// TODO: Implement cleanup verification
\t\t
\t\tBy("Verifying no residual configuration remains")
\t\t// TODO: Verify cleanup was successful
\t}})
}})

// Helper functions for this test suite

func verify{test_name}Configuration(ctx context.Context, clientset kubernetes.Interface, namespace string) error {{
\t// TODO: Implement configuration verification logic
\treturn nil
}}

func cleanup{test_name}Resources(ctx context.Context, oc *exutil.CLI) error {{
\t// TODO: Implement resource cleanup logic
\treturn nil
}}
'''
    return go_content
