---
name: must-gather-analyzer
description: |
  Analyze OpenShift must-gather diagnostic data including cluster operators, pods, nodes,
  and network components. Use when the user asks about cluster health from a must-gather bundle,
  operator status, pod issues, node conditions, or offline diagnostic insights.

  Triggers: "analyze must-gather", "check cluster health", "operator status", "pod issues",
  "node status", "failing pods", "degraded operators", "cluster problems", "crashlooping",
  "network issues", "etcd health", "analyze clusteroperators", "analyze pods", "analyze nodes"

  Based on openshift-eng/ai-helpers must-gather-analyzer skill with workshop MCP integration.
---

# Must-Gather Analyzer

Analyze **offline** OpenShift must-gather bundles. For **live** cluster debugging with `oc`, use the `cluster-debugger` skill instead.

## Workshop MCP integration

This repo provides three ways to analyze must-gather data:

| Method | When to use |
|--------|-------------|
| **Helper scripts** (this skill) | Targeted `oc`-like tables for one component (operators, pods, etcd, etc.) |
| **MCP tool** `analyze_mustgather_bundle` | Full SRE report + anomaly detection + optional LLM enhancement |
| **Web GUI** `/mustgather-analyzer` | Single form runs **Full SRE** + **Focused Scripts** together (or either alone) |

**Recommended workflow:**
1. Run focused scripts below for the component the user asked about.
2. If a holistic report is needed, call MCP `analyze_mustgather_bundle(bundle_path)` or use the web GUI.
3. Cross-reference script output with the SRE report; do not invent findings not in the data.
4. **Do not recommend live `oc`/SSH commands** — must-gather is offline. For live triage use `cluster-debugger`.

Scripts live at: `.cursor/skills/must-gather-analyzer/scripts/` (from [openshift-eng/ai-helpers](https://github.com/openshift-eng/ai-helpers/tree/main/plugins/must-gather/skills/must-gather-analyzer)).

## Must-gather path

Data is usually under a hash-named subdirectory:

```
must-gather/
└── registry-ci-openshift-org-origin-...-sha256-<hash>/
    ├── cluster-scoped-resources/
    ├── namespaces/
    └── network_logs/
```

Pass the **hash subdirectory** (contains `cluster-scoped-resources/` and `namespaces/`), not the outer extract root.

If the user gives a `.tar.gz`, extract first or use MCP `analyze_mustgather_bundle` which handles archives.

## Run analysis scripts

From repo root:

```bash
MG_PATH="<must-gather-hash-subdirectory>"
SCRIPTS=".cursor/skills/must-gather-analyzer/scripts"

# Cluster overview
python3 $SCRIPTS/analyze_clusterversion.py "$MG_PATH"
python3 $SCRIPTS/analyze_clusteroperators.py "$MG_PATH"

# Workloads
python3 $SCRIPTS/analyze_pods.py "$MG_PATH"
python3 $SCRIPTS/analyze_pods.py "$MG_PATH" --problems-only
python3 $SCRIPTS/analyze_pods.py "$MG_PATH" --namespace openshift-etcd

# Infrastructure
python3 $SCRIPTS/analyze_nodes.py "$MG_PATH"
python3 $SCRIPTS/analyze_nodes.py "$MG_PATH" --problems-only
python3 $SCRIPTS/analyze_etcd.py "$MG_PATH"
python3 $SCRIPTS/analyze_network.py "$MG_PATH"
python3 $SCRIPTS/analyze_ovn_dbs.py "$MG_PATH"

# Events, storage, monitoring
python3 $SCRIPTS/analyze_events.py "$MG_PATH" --type Warning
python3 $SCRIPTS/analyze_pvs.py "$MG_PATH"
python3 $SCRIPTS/analyze_prometheus.py "$MG_PATH"
python3 $SCRIPTS/analyze_windows_logs.py "$MG_PATH"   # Windows nodes only
```

## Interpret and report

1. Start with **cluster operators** — system-wide degradation shows here first.
2. Follow **degraded operator → namespace pods → nodes** dependency chain.
3. Use **SINCE** / timestamps to correlate when issues started.
4. Suggest log paths under `namespaces/<ns>/pods/<pod>/` for deeper dives.

## Common scenarios

**Cluster degraded**
1. `analyze_clusteroperators.py`
2. `analyze_pods.py --namespace <operator-ns>`
3. `analyze_nodes.py --problems-only`

**Pods crashlooping**
1. `analyze_pods.py --problems-only`
2. `analyze_nodes.py` for hosting node pressure
3. Point to pod logs in the bundle

**Network issues**
1. `analyze_network.py`
2. `analyze_pods.py --namespace openshift-ovn-kubernetes`
3. `analyze_ovn_dbs.py` if OVN-Kubernetes

## Output format

Scripts emit summary statistics (emoji indicators) and `oc`-like tables. Example:

```
SUMMARY: 25/28 operators healthy
  ⚠️  3 operators with issues
  ❌ 2 degraded
```

## Related

- **Live cluster:** `cluster-debugger` skill → MCP `debug_openshift_cluster`
- **Upstream source:** https://github.com/openshift-eng/ai-helpers/tree/main/plugins/must-gather/skills/must-gather-analyzer
