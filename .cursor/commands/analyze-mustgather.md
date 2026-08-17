# Analyze must-gather bundle

Use the `analyze_mustgather_bundle` MCP tool to analyze this offline must-gather bundle.

Bundle path or URL: $ARGUMENTS

Steps:
1. Resolve and extract the bundle if it is a tar/zip file or URL
2. Identify the primary root cause (upgrade stuck, operator degraded, pod crash, etc.)
3. Summarize evidence from clusterversion, operators, pods, logs, and events
4. Provide remediation steps using bundle paths (no live cluster required)

If the path is a Prow/gcsweb URL, download it first.
