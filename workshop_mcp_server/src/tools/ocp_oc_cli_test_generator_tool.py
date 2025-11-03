"""OpenShift OC CLI Test Case Generator tool for the MCP Server.

This tool generates detailed manual testing guides with step-by-step instructions
for OpenShift components. Perfect for manual testing, documentation, and automation.
"""

from typing import Any, Dict, Optional

from workshop_mcp_server.utils.pylogger import get_python_logger

logger = get_python_logger()


def generate_oc_cli_test(
    feature: str,
    component: str,
    scenario: str,
    namespace: Optional[str] = None,
    api_version: Optional[str] = None,
    description: Optional[str] = None,
    include_cleanup: bool = True,
    verbose: bool = True,
) -> Dict[str, Any]:
    """Generate detailed manual testing guide for OpenShift testing.

    TOOL_NAME=generate_oc_cli_test
    DISPLAY_NAME=OC CLI Test Guide Generator
    USECASE=Generate comprehensive manual testing guides with step-by-step oc CLI commands
    INSTRUCTIONS=1. Provide feature, component, and scenario, 2. Optionally specify namespace, 3. Receive detailed testing guide with manual steps and automation script
    INPUT_DESCRIPTION=feature (str): Feature being tested, component (str): OCP component, scenario (str): Test scenario, namespace (str, optional): Target namespace, api_version (str, optional): API version, description (str, optional): Additional context, include_cleanup (bool): Include cleanup steps (default: true), verbose (bool): Include verbose output (default: true)
    OUTPUT_DESCRIPTION=Dictionary with generated manual testing guide, automation script, and metadata
    EXAMPLES=generate_oc_cli_test("Event TTL", "kube-apiserver", "Verify eventTTLMinutes configuration"), generate_oc_cli_test("Pod Security", "pod-security-admission", "Test restricted policy", namespace="test-security")
    PREREQUISITES=oc CLI installed, cluster access
    RELATED_TOOLS=generate_ocp_test_case, execute_ocp_test

    This tool generates production-ready testing guides that include:
    - Step-by-step manual testing instructions
    - Expected outputs for each step
    - Verification commands
    - Complete automation script
    - Troubleshooting section
    - Important notes and tips

    Args:
        feature: Feature or capability being tested
        component: OpenShift component (e.g., kube-apiserver, oauth, registry)
        scenario: Specific test scenario description
        namespace: Target namespace (optional, generates unique name if not provided)
        api_version: Kubernetes API version (optional)
        description: Additional description or context (optional)
        include_cleanup: Include cleanup steps at the end (default: True)
        verbose: Include verbose output and logging (default: True)

    Returns:
        Dictionary containing the generated testing guide with metadata

    Raises:
        ValueError: If inputs are invalid or incomplete
    """
    try:
        # Validate inputs
        if not feature or not component or not scenario:
            raise ValueError("feature, component, and scenario are required fields")

        logger.info(f"Generating detailed test guide for {component}/{feature}")

        # Generate namespace name if not provided
        if not namespace:
            namespace = f"test-{component.lower().replace('_', '-')}-${{RANDOM}}"

        # Generate the testing guide
        guide = _generate_detailed_test_guide(
            feature=feature,
            component=component,
            scenario=scenario,
            namespace=namespace,
            api_version=api_version,
            description=description,
            include_cleanup=include_cleanup,
            verbose=verbose,
        )

        return {
            "status": "success",
            "format": "markdown",
            "feature": feature,
            "component": component,
            "scenario": scenario,
            "test_guide": guide,
            "metadata": {
                "namespace": namespace,
                "api_version": api_version or "N/A",
                "includes_cleanup": include_cleanup,
                "verbose_mode": verbose,
            },
            "usage_instructions": {
                "save_as": f"manual_test_{component.lower().replace('-', '_')}_{feature.lower().replace(' ', '_')}.md",
                "view": "Open in markdown viewer or text editor",
                "execute_manual_steps": "Follow step-by-step instructions in the guide",
                "execute_automation_script": "Copy the 'Quick Verification Script' section and run it",
            },
            "message": f"Successfully generated detailed test guide for {feature}",
        }

    except Exception as e:
        logger.error(f"Error generating test guide: {e}")
        return {
            "status": "error",
            "error": str(e),
            "message": "Failed to generate test guide",
        }


def _generate_detailed_test_guide(
    feature: str,
    component: str,
    scenario: str,
    namespace: str,
    api_version: Optional[str],
    description: Optional[str],
    include_cleanup: bool,
    verbose: bool,
) -> str:
    """Generate comprehensive manual testing guide with step-by-step instructions."""

    desc_str = description or f"Test {component} {feature} functionality"
    component_normalized = component.lower().replace("_", "-")
    feature_normalized = feature.lower().replace(" ", "-")

    guide = f'''# Manual {feature} Testing Guide

This guide provides step-by-step `oc` CLI commands to manually test the {feature} feature.

## Prerequisites

- Access to an OpenShift cluster with admin privileges
- `oc` CLI tool installed and logged in
- `jq` installed for JSON parsing (optional but recommended)

## Test Steps

### Step 1: Check Current Component Status

```bash
# Get current {component} status
oc get {component_normalized} cluster -o yaml 2>/dev/null || oc get {component_normalized} 2>/dev/null || echo "Component check N/A"

# Check if component is healthy
oc get co | grep -i {component_normalized} || echo "Cluster operator check N/A"

# Get component pods (if applicable)
oc get pods -n openshift-{component_normalized} 2>/dev/null || echo "No dedicated namespace for {component}"
```

### Step 2: Verify Prerequisites

```bash
# Verify cluster access
oc whoami
oc cluster-info | head -1

# Check permissions
oc auth can-i create namespace
oc auth can-i patch {component_normalized}

# Verify oc version
oc version
```

### Step 3: Create Test Namespace

```bash
# Create test namespace with timestamp
TEST_NS="{namespace.replace('${RANDOM}', '$(date +%s)')}"
oc create namespace $TEST_NS

# Label namespace for identification
oc label namespace $TEST_NS test-purpose=manual-testing feature={feature_normalized}

# Verify namespace creation
oc get namespace $TEST_NS
oc describe namespace $TEST_NS
```

### Step 4: Configure {component} for Testing

```bash
# Check current {component} configuration
oc get {component_normalized} cluster -o yaml 2>/dev/null || echo "Configuration check: Manual verification required"

# Patch {component} with test configuration (example - adjust as needed)
# IMPORTANT: Review and customize this patch for your specific test
oc patch {component_normalized} cluster --type=merge -p '{{
  "spec": {{
    "testSetting": "value"
  }}
}}' 2>/dev/null || echo "Patch may not be applicable for this component"

# Verify configuration was applied
oc get {component_normalized} cluster -o json 2>/dev/null | jq '.spec' || echo "Verification via manual inspection required"

# Monitor component rollout (if applicable)
watch -n 5 'oc get pods -n openshift-{component_normalized} 2>/dev/null || echo "Monitoring: Check component pods manually"'
```

**Expected:** Configuration should be updated successfully.

### Step 5: Create Test Resources

```bash
# Create test pod in namespace
cat <<EOF | oc create -f -
apiVersion: v1
kind: Pod
metadata:
  name: test-{feature_normalized}-pod
  namespace: $TEST_NS
  labels:
    test: {feature_normalized}
    component: {component_normalized}
spec:
  containers:
  - name: test-container
    image: registry.access.redhat.com/ubi8/ubi-minimal:latest
    command: ["sh", "-c", "echo 'Testing {feature}' && sleep 30"]
  restartPolicy: Never
EOF

# Verify pod creation
oc get pod test-{feature_normalized}-pod -n $TEST_NS

# Wait for pod to start
sleep 10

# Check pod status
oc get pod test-{feature_normalized}-pod -n $TEST_NS -o wide

# Get pod logs
oc logs test-{feature_normalized}-pod -n $TEST_NS
```

**Expected:** Pod should be created and reach Running or Completed state.

### Step 6: Verify {feature} Behavior

```bash
# Check events related to test
oc get events -n $TEST_NS --sort-by='.lastTimestamp'

# Verify {feature} is working as expected
oc get events -n $TEST_NS --field-selector involvedObject.name=test-{feature_normalized}-pod

# Describe pod to see details
oc describe pod test-{feature_normalized}-pod -n $TEST_NS

# Check component logs (if applicable)
COMPONENT_POD=$(oc get pods -n openshift-{component_normalized} -l app={component_normalized} -o jsonpath='{{.items[0].metadata.name}}' 2>/dev/null || echo "N/A")
if [ "$COMPONENT_POD" != "N/A" ]; then
  echo "Component pod: $COMPONENT_POD"
  oc logs $COMPONENT_POD -n openshift-{component_normalized} --tail=50
fi
```

**Expected:**
- Events should show normal pod lifecycle
- No errors in component logs
- {feature} behavior is as expected

### Step 7: Perform Specific {feature} Validation

```bash
# Test-specific validation commands
# Customize based on what {feature} should do

# Example: Check if configuration is in ConfigMap
oc get configmap -n openshift-{component_normalized} -o yaml | grep -i "{feature_normalized}" || echo "Feature check in ConfigMap"

# Example: Verify via API
oc get {component_normalized} cluster -o json | jq '.status' 2>/dev/null || echo "Status check via manual inspection"

# Example: Check cluster operator status
oc get co | grep -i {component_normalized}
oc get co $(oc get co | grep -i {component_normalized} | awk '{{print $1}}') -o yaml 2>/dev/null || echo "Detailed CO status N/A"
```

### Step 8: Monitor and Wait (If Applicable)

```bash
# If the test requires waiting for {feature} to take effect
echo "Waiting for {feature} to take effect..."
echo "Monitor the following:"

# Monitor pods
watch -n 5 'oc get pods -n $TEST_NS'

# Monitor events
watch -n 10 'oc get events -n $TEST_NS --sort-by=.lastTimestamp | tail -10'

# Monitor component
watch -n 5 'oc get pods -n openshift-{component_normalized} 2>/dev/null || echo "Component monitoring N/A"'
```

### Step 9: Verify Final State

```bash
# Final verification checks
echo "=== Final Verification ==="

# Check test resources still exist (or have been cleaned up as expected)
oc get all -n $TEST_NS

# Verify {feature} behavior after waiting
oc get pod test-{feature_normalized}-pod -n $TEST_NS -o yaml | grep -A5 status

# Check for any errors
oc get events -n $TEST_NS --field-selector type=Warning

# Verify component health
oc get co | grep -i {component_normalized} || echo "Component operator check N/A"
```

**Expected:** All resources should be in expected state based on {feature} behavior.

### Step 10: Cleanup

```bash
# Delete test namespace
oc delete namespace $TEST_NS

# Verify deletion
oc get namespace $TEST_NS 2>&1 | grep -i "NotFound" && echo "✅ Namespace deleted successfully"

# Restore original configuration (if you changed component config)
# IMPORTANT: Only run if you modified component configuration in Step 4
oc patch {component_normalized} cluster --type=merge -p '{{
  "spec": {{
    "testSetting": null
  }}
}}' 2>/dev/null || echo "Config restore: Verify manually if needed"

# Wait for component rollout (if applicable)
watch -n 5 'oc get pods -n openshift-{component_normalized} 2>/dev/null || echo "Rollout monitoring N/A"'
```

---

## Quick Verification Script

Here's a complete script to automate the verification:

```bash
#!/bin/bash
set -e

# Configuration
FEATURE="{feature}"
COMPONENT="{component}"
SCENARIO="{scenario}"
TEST_NS="test-{component_normalized}-$(date +%s)"

echo "=== {feature} Manual Test ==="
echo "Component: $COMPONENT"
echo "Test Namespace: $TEST_NS"
echo ""

# Step 1: Check prerequisites
echo "Step 1: Checking prerequisites..."
if ! command -v oc &> /dev/null; then
  echo "❌ oc CLI not found"
  exit 1
fi
echo "✅ oc CLI found: $(oc version --client -o json | jq -r '.clientVersion.gitVersion' 2>/dev/null || echo 'version unknown')"

if ! oc cluster-info &> /dev/null; then
  echo "❌ Not connected to cluster"
  exit 1
fi
echo "✅ Connected to cluster"

# Step 2: Create test namespace
echo ""
echo "Step 2: Creating test namespace..."
oc create namespace $TEST_NS
oc label namespace $TEST_NS test-purpose=automated-testing
echo "✅ Namespace created: $TEST_NS"

# Step 3: Create test resources
echo ""
echo "Step 3: Creating test pod..."
cat <<EOF | oc create -f -
apiVersion: v1
kind: Pod
metadata:
  name: test-{feature_normalized}-pod
  namespace: $TEST_NS
spec:
  containers:
  - name: test
    image: registry.access.redhat.com/ubi8/ubi-minimal:latest
    command: ["sh", "-c", "echo 'Testing {feature}' && sleep 30"]
  restartPolicy: Never
EOF

echo "✅ Test pod created"

# Step 4: Wait and verify
echo ""
echo "Step 4: Waiting for pod to complete..."
sleep 15

POD_STATUS=$(oc get pod test-{feature_normalized}-pod -n $TEST_NS -o jsonpath='{{.status.phase}}' 2>/dev/null || echo "Unknown")
echo "Pod status: $POD_STATUS"

if [[ "$POD_STATUS" == "Running" ]] || [[ "$POD_STATUS" == "Succeeded" ]]; then
  echo "✅ Pod is running/completed"
else
  echo "⚠️  Pod status: $POD_STATUS"
fi

# Step 5: Check events
echo ""
echo "Step 5: Checking events..."
EVENT_COUNT=$(oc get events -n $TEST_NS --field-selector involvedObject.name=test-{feature_normalized}-pod 2>/dev/null | wc -l)
echo "Events found: $EVENT_COUNT"

if [ $EVENT_COUNT -gt 1 ]; then
  echo "✅ Events recorded for test pod"
  oc get events -n $TEST_NS --field-selector involvedObject.name=test-{feature_normalized}-pod --sort-by=.lastTimestamp
else
  echo "⚠️  No events found"
fi

# Step 6: Verify {feature} specific behavior
echo ""
echo "Step 6: Verifying {feature} behavior..."
echo "Scenario: {scenario}"
echo "✅ Manual verification required for specific {feature} behavior"

# Step 7: Cleanup
echo ""
echo "Step 7: Cleaning up..."
oc delete namespace $TEST_NS --wait=false
echo "✅ Cleanup initiated for namespace: $TEST_NS"

echo ""
echo "=== Test Completed ==="
echo "Review the output above to verify {feature} is working as expected"
```

---

## Important Notes

1. **Customization Required**: This is a template guide. You MUST customize the specific commands based on what {feature} actually does.

2. **Configuration Changes**: If you modify cluster-level configuration (like in Step 4), ensure you restore it in cleanup.

3. **Permissions**: Some operations may require cluster-admin privileges.

4. **Timing**: Add appropriate wait times between steps if {feature} requires time to take effect.

5. **Validation**: The verification steps (Step 6-7) need to be customized based on expected {feature} behavior.

## Troubleshooting

### Issue: Cannot create namespace

```bash
# Check permissions
oc auth can-i create namespace

# Try with specific project
oc new-project $TEST_NS
```

### Issue: Pod not starting

```bash
# Check pod details
oc describe pod test-{feature_normalized}-pod -n $TEST_NS

# Check events
oc get events -n $TEST_NS --sort-by=.lastTimestamp | tail -20

# Check node status
oc get nodes
```

### Issue: Component not responding

```bash
# Check component operator
oc get co | grep -i {component_normalized}
oc get co $(oc get co | grep -i {component_normalized} | awk '{{print $1}}') -o yaml

# Check component pods
oc get pods -n openshift-{component_normalized}

# Check component logs
oc logs -n openshift-{component_normalized} -l app={component_normalized} --tail=100
```

### Issue: Configuration not applied

```bash
# Verify the patch was accepted
oc get {component_normalized} cluster -o yaml | grep -A10 spec

# Check operator logs
oc logs -n openshift-{component_normalized}-operator deployment/{component_normalized}-operator --tail=100 2>/dev/null || echo "Operator logs N/A"

# Force reconciliation (if applicable)
oc delete pod -n openshift-{component_normalized} -l app={component_normalized} --wait=false
```

---

**Need Help?**
- Review OpenShift documentation for {component}
- Check cluster operator status: `oc get co`
- Review must-gather if issues persist
- Consult Red Hat support or community forums

---

**Test Information:**
- **Feature**: {feature}
- **Component**: {component}
- **Scenario**: {scenario}
- **Generated**: $(date)
'''

    return guide
