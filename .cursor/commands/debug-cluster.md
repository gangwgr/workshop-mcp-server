# Debug OpenShift cluster

Use the `debug_openshift_cluster` MCP tool to investigate this issue on the live cluster.

Issue: $ARGUMENTS

Steps:
1. Run focused `oc` diagnostics for the reported component/namespace
2. Summarize root cause from actual command output
3. Provide remediation steps and a Go/Ginkgo test case if appropriate

If kubeconfig is needed, ask the user for the path before running commands.
