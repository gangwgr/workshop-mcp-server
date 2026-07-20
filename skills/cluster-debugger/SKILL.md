---
name: cluster-debugger
description: |
  Debug live OpenShift/Kubernetes clusters using oc CLI diagnostics, issue triage, and fix
  recommendations. Use when the user has cluster access and describes runtime problems
  (pods failing, operators degraded, API errors, upgrade stuck, auth issues).

  Triggers: "debug cluster", "cluster issue", "crashloop", "operator degraded", "oc debug",
  "pod not starting", "API server", "etcd unhealthy", "fix cluster", "troubleshoot openshift"

  Complements must-gather-analyzer (offline bundles). Use this skill for live clusters.
---

# OpenShift Cluster Debugger

Debug **live** clusters with `oc`. For **offline** must-gather analysis, use the `must-gather-analyzer` skill.

## Workshop MCP integration

| Method | When to use |
|--------|-------------|
| **MCP tool** `debug_openshift_cluster` | AI diagnosis + fix steps + optional Go/shell test case generation |
| **Web GUI** `/cluster-debugger` | AI diagnosis **or** run focused live `oc` workflows via **Focused oc Triage** tab |
| **Manual oc** (this skill) | Step-by-step triage when MCP/GUI unavailable or user wants raw commands |

**Prerequisites:** `oc` logged in, `KUBECONFIG` set (or pass `kubeconfig_path` to MCP tool).

## Choose the right tool

| Situation | Use |
|-----------|-----|
| User has must-gather tarball only | `must-gather-analyzer` skill |
| User has live cluster access | This skill or `debug_openshift_cluster` |
| Need automated test case from a bug | `debug_openshift_cluster(include_test_case=True)` |
| Need SRE-style bundle report | `analyze_mustgather_bundle` |

## Initial triage (always run first)

```bash
oc get clusterversion
oc get clusteroperators
oc get co -o json | jq -r '.items[] | select(.status.conditions[]? | select(.type=="Degraded" and .status=="True")) | .metadata.name'
oc get nodes
oc get pods -A | grep -vE 'Running|Completed'
```

## Issue-based workflows

### Operators degraded

```bash
oc describe clusteroperator <name>
oc get pods -n openshift-<component> -o wide
oc logs -n openshift-<component> <pod> --previous 2>/dev/null | tail -80
oc get events -n openshift-<component> --sort-by='.lastTimestamp' | tail -20
```

### Pod crashloop / not ready

```bash
oc describe pod -n <ns> <pod>
oc logs -n <ns> <pod> --previous
oc get events -n <ns> --field-selector involvedObject.name=<pod>
```

### API / control plane

For dedicated API server triage, use the **`apiserver-debugger`** skill or GUI presets
**API Not Responding** / **API Server Full Debug**.

```bash
oc get clusteroperator kube-apiserver
oc get pods -n openshift-kube-apiserver -o wide
oc get --raw /healthz
oc get pods -n openshift-etcd
oc get etcd cluster -o yaml
oc adm inspect ns/openshift-etcd  # if deeper dump needed
```

### Upgrade stuck

```bash
oc get clusterversion -o yaml
oc get clusteroperators
oc adm upgrade --include-not-ready
```

### Authentication / OAuth

```bash
oc get pods -n openshift-authentication
oc get oauth cluster -o yaml
oc get authentication cluster -o yaml
```

### Network (OVN)

```bash
oc get pods -n openshift-ovn-kubernetes
oc get network.config cluster -o yaml
oc get podnetworkconnectivitychecks -A
```

## MCP tool usage

```
debug_openshift_cluster(
  issue_description="etcd pods crashlooping after upgrade",
  namespace="openshift-etcd",
  component="etcd",
  include_test_case=True
)
```

Returns: diagnostic summary, `oc` commands run, fix recommendations, optional Ginkgo/shell test stubs.

## Report format

When answering the user:

1. **Primary issue** — one sentence
2. **Evidence** — command output or MCP findings (quote facts only)
3. **Impact** — what is broken for users/workloads
4. **Immediate actions** — ordered `oc` commands or fixes
5. **Root cause** — hypothesis with confidence (High/Medium/Low)
6. **Next steps** — must-gather, logs, Jira, escalation

## Safety

- Do not run destructive commands (`oc delete`, `etcdctl` member remove) without explicit user approval.
- State when data is missing or commands failed (auth, RBAC, timeout).
- If live access fails, suggest collecting must-gather and switching to `must-gather-analyzer`.

## Related

- **API server focus:** `apiserver-debugger` skill
- **Offline analysis:** `must-gather-analyzer` skill
- **MCP tools:** `debug_openshift_cluster`, `analyze_mustgather_bundle`
- **Web GUI:** http://127.0.0.1:5001/cluster-debugger
