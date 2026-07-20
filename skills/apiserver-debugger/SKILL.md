---
name: apiserver-debugger
description: |
  Debug OpenShift/Kubernetes API server issues on live clusters using focused oc diagnostics.
  Use when the user reports API timeouts, 503 errors, kube-apiserver crashloops, slow API,
  authentication failures against the API, or cluster-kube-apiserver-operator degradation.

  Triggers: "apiserver", "api server", "kube-apiserver", "API timeout", "503", "API not responding",
  "unable to handle the request", "openshift-apiserver", "kube-apiserver-operator"

  Complements cluster-debugger (general triage) and must-gather-analyzer (offline bundles).
---

# API Server Debugger

Debug **live** kube-apiserver and openshift-apiserver issues. For general cluster triage use `cluster-debugger`; for offline bundles use `must-gather-analyzer`.

## Workshop integration

| Method | When to use |
|--------|-------------|
| **Web GUI** `/cluster-debugger` → **Focused oc Triage** | Run API server presets/workflows with raw `oc` output |
| **MCP tool** `debug_openshift_cluster` | AI diagnosis with issue description like "API server not responding" |
| **This skill** | Step-by-step API server triage and interpretation |

**Prerequisites:** `oc` logged in; API may be slow or partially broken — start with lightweight health checks.

## OpenShift API server components

| Component | Namespace | ClusterOperator |
|-----------|-----------|-----------------|
| **kube-apiserver** (Kubernetes API) | `openshift-kube-apiserver` | `kube-apiserver` |
| **kube-apiserver operator** | `openshift-kube-apiserver-operator` | `kube-apiserver` |
| **openshift-apiserver** (OpenShift API aggregation) | `openshift-apiserver` | `openshift-apiserver` |
| **oauth-apiserver** | `openshift-oauth-apiserver` | `authentication` |

## Quick health check (run first)

```bash
oc get clusteroperator kube-apiserver
oc get pods -n openshift-kube-apiserver -o wide
oc get --raw /healthz
oc get --raw /livez?verbose
oc get --raw /readyz?verbose
```

**Healthy signals:** all kube-apiserver pods `Running`, `/healthz` returns `ok`, operator `Available=True` and `Degraded=False`.

## Workflows by symptom

### API not responding / timeouts

```bash
oc get --raw /healthz
oc get --raw /livez?verbose
oc get pods -n openshift-kube-apiserver -l app=openshift-kube-apiserver -o wide
oc logs -n openshift-kube-apiserver -l app=openshift-kube-apiserver --tail=80 --prefix=true
oc get events -n openshift-kube-apiserver --sort-by=.lastTimestamp | tail -30
```

Then check etcd (API depends on etcd):

```bash
oc get pods -n openshift-etcd -o wide
oc get etcd cluster -o yaml
```

### kube-apiserver operator degraded

```bash
oc describe clusteroperator kube-apiserver
oc get pods -n openshift-kube-apiserver-operator -o wide
oc get kubeapiserver cluster -o yaml
oc get events -n openshift-kube-apiserver-operator --sort-by=.lastTimestamp | tail -20
```

### Single apiserver pod crashlooping

```bash
oc get pods -n openshift-kube-apiserver -o wide
oc describe pod -n openshift-kube-apiserver <pod-name>
oc logs -n openshift-kube-apiserver <pod-name> --tail=100
oc logs -n openshift-kube-apiserver <pod-name> --previous --tail=50
```

### Auth / 401 / 403 against API

```bash
oc whoami
oc get clusteroperator authentication
oc get pods -n openshift-authentication -o wide
oc get pods -n openshift-oauth-apiserver -o wide
oc get oauth cluster -o yaml
```

### openshift-apiserver issues (OpenShift resources)

```bash
oc get clusteroperator openshift-apiserver
oc get pods -n openshift-apiserver -o wide
oc get apiserver cluster -o yaml
oc logs -n openshift-apiserver --tail=80 --prefix=true
```

### After upgrade / revision rollout stuck

```bash
oc get clusterversion
oc describe clusteroperator kube-apiserver
oc get pods -n openshift-kube-apiserver -o wide
oc get kubeapiserver cluster -o yaml | grep -A5 observedGeneration
```

## Interpretation guide

1. **All apiserver pods down** → check nodes hosting control plane, etcd quorum, disk/memory on masters.
2. **Some pods down** → describe failing pod; check `Revision` rollout and operator status.
3. **`/healthz` fails but pods Running** → check readiness probes, etcd connectivity, certificate expiry in logs.
4. **503 / timeout with healthy pods** → check etcd latency, API request rate, admission webhook timeouts.
5. **401/403** → authentication operator, OAuth, RBAC — not always kube-apiserver root cause.

## Web GUI presets

On `/cluster-debugger` → **Focused oc Triage**:

- **API Server Not Responding** — health endpoints, pods, logs
- **API Server Full Debug** — operator, config, connectivity, logs, events
- **OpenShift API Server** — openshift-apiserver operator and pods

## Report format

1. **API status** — health endpoints + pod count
2. **Operator state** — kube-apiserver CO conditions
3. **Evidence** — log lines, events (quote only what you see)
4. **Likely cause** — etcd vs apiserver vs auth vs node
5. **Next commands** — deeper pod describe, must-gather, master node SOS

## Safety

- Do not delete apiserver pods or etcd members without explicit approval.
- Avoid `oc adm drain` on control plane nodes during investigation.
- If API is completely down, use node SSH / must-gather from bastion.

## Related

- **General cluster:** `cluster-debugger` skill
- **Offline:** `must-gather-analyzer` skill
- **MCP:** `debug_openshift_cluster(issue_description="API server not responding")`
