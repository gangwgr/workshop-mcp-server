"""Must-Gather AI Analyzer - Professional OpenShift SRE Diagnostic Tool.

The Must-Gather AI Analyzer is an OpenShift Site Reliability Engineer (SRE) and cluster 
administrator with deep expertise in diagnosing cluster failures. It analyzes must-gather 
bundles to provide structured, actionable diagnostic reports for production troubleshooting.

Persona: Professional OpenShift SRE
Tone: Professional, concise, and solution-oriented
Audience: OpenShift administrators troubleshooting production issues
Constraint: Base all insights strictly on provided data, state uncertainty if data is missing
"""

import os
import json
import re
import tarfile
import zipfile
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

from workshop_mcp_server.utils.pylogger import get_python_logger

logger = get_python_logger()

@dataclass
class MustGatherIssue:
    """Represents an issue found in must-gather analysis"""
    severity: str  # critical, warning, info
    category: str  # network, storage, compute, auth, etc.
    component: str  # specific component like etcd, authentication-operator, node name, etc.
    title: str
    description: str
    file_path: str
    line_number: Optional[int] = None
    suggested_fix: Optional[str] = None
    documentation_link: Optional[str] = None

@dataclass
class ClusterHealth:
    """Represents overall cluster health assessment"""
    status: str  # healthy, degraded, critical
    node_count: int
    pod_count: int
    namespace_count: int
    issues_found: int
    critical_issues: int
    warnings: int
    summary: str

@dataclass
class AnomalyDetectionResult:
    """Represents anomaly detection results"""
    status: str  # NORMAL, ANOMALOUS
    score: float  # 0.0 to 1.0, higher means more anomalous
    severity: str  # 🟢 Normal / 🟡 Warning / 🔴 Critical
    primary_anomalies: List[str]
    confidence: str  # High, Medium, Low

@dataclass
class SREDiagnosticReport:
    """Professional SRE diagnostic report structure following incident response methodology"""
    primary_issue: str
    evidence: str
    impact: List[str]
    immediate_actions: List[str]
    root_cause_summary: str
    severity_emoji: str
    confidence_level: str
    
    # Legacy fields for backward compatibility
    anomaly_explanation: str = ""
    long_term_fixes: List[str] = None
    next_steps: List[str] = None
    limitations: List[str] = None
    key_metrics: Dict[str, Any] = None
    relevant_snippets: List[str] = None
    
    def __post_init__(self):
        if self.long_term_fixes is None:
            self.long_term_fixes = []
        if self.next_steps is None:
            self.next_steps = []
        if self.limitations is None:
            self.limitations = []
        if self.key_metrics is None:
            self.key_metrics = {}
        if self.relevant_snippets is None:
            self.relevant_snippets = []

class MustGatherAnalyzer:
    """Analyzes OpenShift must-gather bundles"""
    
    def __init__(self):
        self.issues: List[MustGatherIssue] = []
        self.cluster_info: Dict[str, Any] = {}
        self.log_patterns = self._load_error_patterns()
        self.key_features: Dict[str, Any] = {}
        self.relevant_snippets: List[str] = []
        self.operator_conditions: Dict[str, Any] = {}
        self.node_states: Dict[str, Any] = {}
    
    def _extract_component_from_path(self, file_path: str) -> str:
        """Extract component name from file path"""
        try:
            # Normalize path and extract meaningful component name
            path_parts = file_path.replace('\\', '/').split('/')
            
            # Look for known OpenShift component patterns
            for part in path_parts:
                # Operator patterns
                if 'operator' in part.lower():
                    return part
                # Control plane components
                if part in ['etcd', 'apiserver', 'controller-manager', 'scheduler']:
                    return part
                # Authentication components
                if part in ['authentication', 'oauth']:
                    return part
                # Network components
                if part in ['sdn', 'ovn', 'network']:
                    return part
                # Storage components
                if part in ['storage', 'csi']:
                    return part
                # Cluster operators
                if part.endswith('-operator'):
                    return part
                # Node components
                if part.startswith('node-'):
                    return part
                # Namespace patterns
                if part.startswith('openshift-'):
                    return part.replace('openshift-', '')
            
            # Fallback to basename without extension
            basename = os.path.basename(file_path)
            if '.' in basename:
                return basename.split('.')[0]
            return basename if basename else 'unknown'
            
        except Exception:
            return 'unknown'
        
    def _load_error_patterns(self) -> Dict[str, List[str]]:
        """Load common OpenShift error patterns"""
        return {
            "critical": [
                r"FATAL|Fatal|fatal",
                r"panic:",
                r"oom-killer",
                r"Out of memory",
                r"No space left on device",
                r"Failed to pull image",
                r"ImagePullBackOff",
                r"CrashLoopBackOff",
                r"Failed to schedule",
                r"Insufficient cpu|Insufficient memory",
                r"etcd cluster is unavailable",
                r"API server is down",
                r"Control plane is unhealthy"
            ],
            "warning": [
                r"WARNING|Warning|warning",
                r"WARN|Warn|warn",
                r"Failed to.*retry",
                r"Timeout.*exceeded",
                r"Connection refused",
                r"Certificate.*expired",
                r"Pod.*Pending",
                r"Node.*NotReady",
                r"Volume.*failed to mount",
                r"DNS resolution failed",
                r"Network.*unreachable"
            ],
            "info": [
                r"INFO|Info|info",
                r"Successfully",
                r"Started",
                r"Stopped",
                r"Created",
                r"Deleted"
            ]
        }

    def analyze_bundle(self, bundle_path: str) -> Dict[str, Any]:
        """Analyze a must-gather bundle"""
        try:
            logger.info(f"Starting analysis of must-gather bundle: {bundle_path}")
            
            # Extract bundle if compressed
            extracted_path = self._extract_bundle(bundle_path)
            
            # Perform comprehensive file discovery and analysis
            logger.info(f"Starting comprehensive analysis of {extracted_path}")
            
            # First, discover all available files in the bundle
            self._discover_bundle_structure(extracted_path)
            
            # Analyze different components systematically
            self._analyze_cluster_info(extracted_path)
            self._analyze_nodes(extracted_path)
            self._analyze_pods(extracted_path)
            self._analyze_events(extracted_path)
            self._analyze_operators(extracted_path)
            self._analyze_logs(extracted_path)
            self._analyze_network(extracted_path)
            self._analyze_storage(extracted_path)
            
            # Deep scan for any YAML/JSON files we might have missed
            self._deep_scan_all_files(extracted_path)
            
            # Generate health assessment
            health = self._assess_cluster_health()
            
            # Perform anomaly detection
            anomaly_result = self._detect_anomalies()
            
            # Generate SRE diagnostic report
            sre_report = self._generate_sre_diagnostic_report(health, anomaly_result)
            
            # Generate traditional report for compatibility
            report = self._generate_report(health)
            
            logger.info(f"Analysis complete. Found {len(self.issues)} issues")
            
            return {
                "status": "success",
                "bundle_path": bundle_path,
                "cluster_health": health.__dict__,
                "anomaly_detection_result": anomaly_result.__dict__,
                "sre_diagnostic_report": sre_report.__dict__,
                "issues_found": len(self.issues),
                "issues": [issue.__dict__ for issue in self.issues],
                "report": report,
                "cluster_info": self.cluster_info,
                "key_features": self.key_features,
                "relevant_snippets": self.relevant_snippets[:10],  # Limit for readability
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing must-gather bundle: {e}")
            return {
                "status": "error",
                "error": str(e),
                "bundle_path": bundle_path,
                "timestamp": datetime.now().isoformat()
            }

    def _extract_bundle(self, bundle_path: str) -> str:
        """Extract compressed must-gather bundle"""
        if not os.path.exists(bundle_path):
            raise FileNotFoundError(f"Must-gather bundle not found: {bundle_path}")
            
        # If it's already a directory, return it
        if os.path.isdir(bundle_path):
            logger.info(f"Bundle is already a directory: {bundle_path}")
            return bundle_path
            
        extract_dir = bundle_path + "_extracted"
        
        # Remove existing extraction if it exists
        if os.path.exists(extract_dir):
            shutil.rmtree(extract_dir)
        
        logger.info(f"Extracting bundle {bundle_path} to {extract_dir}")
        
        # Extract based on file type
        try:
            if bundle_path.endswith(('.tar.gz', '.tgz')):
                with tarfile.open(bundle_path, 'r:gz') as tar:
                    tar.extractall(extract_dir)
                    logger.info(f"Extracted {len(tar.getnames())} files from tar.gz")
            elif bundle_path.endswith('.tar'):
                with tarfile.open(bundle_path, 'r') as tar:
                    tar.extractall(extract_dir)
                    logger.info(f"Extracted {len(tar.getnames())} files from tar")
            elif bundle_path.endswith('.zip'):
                with zipfile.ZipFile(bundle_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_dir)
                    logger.info(f"Extracted {len(zip_ref.namelist())} files from zip")
            else:
                # Try to detect file type by magic numbers
                with open(bundle_path, 'rb') as f:
                    magic = f.read(4)
                    
                if magic.startswith(b'\x1f\x8b'):  # gzip magic
                    with tarfile.open(bundle_path, 'r:gz') as tar:
                        tar.extractall(extract_dir)
                        logger.info(f"Auto-detected and extracted {len(tar.getnames())} files from gzip")
                elif magic.startswith(b'PK'):  # zip magic
                    with zipfile.ZipFile(bundle_path, 'r') as zip_ref:
                        zip_ref.extractall(extract_dir)
                        logger.info(f"Auto-detected and extracted {len(zip_ref.namelist())} files from zip")
                else:
                    # Assume it's an uncompressed directory
                    logger.warning(f"Unknown file format, treating as directory: {bundle_path}")
                    return bundle_path
        except Exception as e:
            logger.error(f"Failed to extract bundle: {e}")
            raise
            
        # Find the actual must-gather root directory
        extracted_files = os.listdir(extract_dir)
        if len(extracted_files) == 1 and os.path.isdir(os.path.join(extract_dir, extracted_files[0])):
            # Common case: bundle extracts to a single directory
            actual_root = os.path.join(extract_dir, extracted_files[0])
            logger.info(f"Found must-gather root directory: {actual_root}")
            return actual_root
            
        logger.info(f"Using extraction directory as root: {extract_dir}")
        return extract_dir

    def _discover_bundle_structure(self, path: str):
        """Discover and log the structure of the must-gather bundle"""
        try:
            logger.info(f"Discovering bundle structure in: {path}")
            file_count = 0
            yaml_files = 0
            json_files = 0
            log_files = 0
            
            for root, dirs, files in os.walk(path):
                for file in files:
                    file_count += 1
                    if file.endswith(('.yaml', '.yml')):
                        yaml_files += 1
                    elif file.endswith('.json'):
                        json_files += 1
                    elif 'log' in file.lower() or file.endswith('.log'):
                        log_files += 1
            
            logger.info(f"Bundle contains: {file_count} total files, {yaml_files} YAML, {json_files} JSON, {log_files} log files")
            self.key_features.update({
                "total_files": file_count,
                "yaml_files": yaml_files,
                "json_files": json_files,
                "log_files": log_files
            })
            
            # Look for key OpenShift directories
            key_dirs = [
                "cluster-scoped-resources",
                "namespaces", 
                "host_service_logs",
                "audit_logs",
                "network_logs"
            ]
            
            found_dirs = []
            for key_dir in key_dirs:
                full_path = os.path.join(path, key_dir)
                if os.path.exists(full_path):
                    found_dirs.append(key_dir)
                    logger.info(f"Found key directory: {key_dir}")
            
            self.key_features["key_directories"] = found_dirs
            
        except Exception as e:
            logger.error(f"Error discovering bundle structure: {e}")

    def _deep_scan_all_files(self, path: str):
        """Perform deep scan of all files for comprehensive analysis"""
        try:
            logger.info("Starting deep scan of all files")
            scanned_files = 0
            issues_found = 0
            
            for root, dirs, files in os.walk(path):
                for file in files:
                    file_path = os.path.join(root, file)
                    
                    # Skip very large files to avoid memory issues
                    try:
                        file_size = os.path.getsize(file_path)
                        if file_size > 100 * 1024 * 1024:  # Skip files > 100MB
                            continue
                    except:
                        continue
                    
                    if file.endswith(('.yaml', '.yml', '.json')):
                        scanned_files += 1
                        if self._analyze_structured_file(file_path, root.replace(path, "")):
                            issues_found += 1
                    elif 'log' in file.lower() or file.endswith('.log'):
                        scanned_files += 1
                        if self._analyze_log_file_deep(file_path):
                            issues_found += 1
            
            logger.info(f"Deep scan complete: {scanned_files} files scanned, {issues_found} files contained issues")
            self.key_features.update({
                "scanned_files": scanned_files,
                "files_with_issues": issues_found
            })
            
        except Exception as e:
            logger.error(f"Error in deep scan: {e}")

    def _analyze_structured_file(self, file_path: str, relative_dir: str) -> bool:
        """Analyze a YAML or JSON file for issues"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            issues_found = False
            
            # Look for error conditions in the content
            error_patterns = [
                r'status:\s*"?failed"?',
                r'phase:\s*"?failed"?',
                r'condition.*false',
                r'ready:\s*false',
                r'available:\s*false',
                r'degraded:\s*true',
                r'error.*:',
                r'failed.*:',
                r'crashloopbackoff',
                r'imagepullbackoff',
                r'pending',
                r'evicted',
                r'oomkilled',
                r'notready',
                r'unhealthy'
            ]
            
            for pattern in error_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    # Determine severity based on pattern
                    if any(severe in pattern for severe in ['failed', 'degraded', 'crash', 'oom']):
                        severity = "critical"
                    else:
                        severity = "warning"
                    
                    self.issues.append(MustGatherIssue(
                        severity=severity,
                        category="configuration",
                        component=self._extract_component_from_path(file_path),
                        title=f"Issue found in {os.path.basename(file_path)}",
                        description=f"Pattern '{pattern}' found: {matches[0][:100]}",
                        file_path=relative_dir + "/" + os.path.basename(file_path),
                        suggested_fix="Review configuration and logs for detailed troubleshooting"
                    ))
                    issues_found = True
            
            # Add to relevant snippets if it contains interesting data
            if any(keyword in content.lower() for keyword in ['error', 'failed', 'warning', 'critical']):
                self.relevant_snippets.append(f"File: {relative_dir}/{os.path.basename(file_path)}\n{content[:400]}...")
            
            return issues_found
            
        except Exception as e:
            logger.error(f"Error analyzing structured file {file_path}: {e}")
            return False

    def _analyze_log_file_deep(self, file_path: str) -> bool:
        """Deep analysis of log files"""
        try:
            issues_found = False
            error_count = 0
            
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            # Analyze recent lines (last 1000) for efficiency
            recent_lines = lines[-1000:] if len(lines) > 1000 else lines
            
            for line_num, line in enumerate(recent_lines):
                # Count different types of errors
                if re.search(r'(ERROR|FATAL|CRITICAL)', line, re.IGNORECASE):
                    error_count += 1
                    if error_count <= 5:  # Only capture first 5 errors to avoid spam
                        self.issues.append(MustGatherIssue(
                            severity="critical",
                            category="logs",
                            component=self._extract_component_from_path(file_path),
                            title=f"Critical error in {os.path.basename(file_path)}",
                            description=line.strip()[:200],
                            file_path=file_path,
                            line_number=len(lines) - len(recent_lines) + line_num + 1
                        ))
                        issues_found = True
                
                elif re.search(r'(WARN|WARNING)', line, re.IGNORECASE):
                    if error_count <= 3:  # Limit warnings too
                        self.issues.append(MustGatherIssue(
                            severity="warning",
                            category="logs",
                            component=self._extract_component_from_path(file_path),
                            title=f"Warning in {os.path.basename(file_path)}",
                            description=line.strip()[:200],
                            file_path=file_path,
                            line_number=len(lines) - len(recent_lines) + line_num + 1
                        ))
                        issues_found = True
            
            return issues_found
            
        except Exception as e:
            logger.error(f"Error analyzing log file {file_path}: {e}")
            return False

    def _analyze_operators(self, path: str):
        """Analyze cluster operators in detail"""
        try:
            operators_path = os.path.join(path, "cluster-scoped-resources/config.openshift.io/clusteroperators")
            if os.path.exists(operators_path):
                logger.info("Analyzing cluster operators")
                
                for operator_file in os.listdir(operators_path):
                    if operator_file.endswith('.yaml'):
                        operator_path = os.path.join(operators_path, operator_file)
                        with open(operator_path, 'r') as f:
                            content = f.read()
                        
                        operator_name = operator_file.replace('.yaml', '')
                        
                        # Check operator conditions
                        if 'degraded: "true"' in content or 'degraded: true' in content:
                            self.issues.append(MustGatherIssue(
                                severity="critical",
                                category="operators",
                                component=operator_name,
                                title=f"Operator {operator_name} is degraded",
                                description=f"Cluster operator {operator_name} is in degraded state",
                                file_path=f"cluster-scoped-resources/config.openshift.io/clusteroperators/{operator_file}",
                                suggested_fix=f"Check {operator_name} operator logs and configuration"
                            ))
                            
                        if 'available: "false"' in content or 'available: false' in content:
                            self.issues.append(MustGatherIssue(
                                severity="critical",
                                category="operators",
                                component=operator_name,
                                title=f"Operator {operator_name} is unavailable",
                                description=f"Cluster operator {operator_name} is not available",
                                file_path=f"cluster-scoped-resources/config.openshift.io/clusteroperators/{operator_file}",
                                suggested_fix=f"Investigate {operator_name} operator deployment and dependencies"
                            ))
            
            # Also check for operator pods
            operator_namespaces = [
                "openshift-etcd",
                "openshift-kube-apiserver",
                "openshift-kube-controller-manager", 
                "openshift-kube-scheduler",
                "openshift-authentication",
                "openshift-oauth-apiserver"
            ]
            
            for ns in operator_namespaces:
                ns_path = os.path.join(path, f"namespaces/{ns}")
                if os.path.exists(ns_path):
                    self._analyze_namespace_pods(ns_path, ns)
                    
        except Exception as e:
            logger.error(f"Error analyzing operators: {e}")

    def _analyze_namespace_pods(self, ns_path: str, namespace: str):
        """Analyze pods in a specific namespace"""
        try:
            pods_path = os.path.join(ns_path, "core/pods")
            if os.path.exists(pods_path):
                for pod_file in os.listdir(pods_path):
                    if pod_file.endswith('.yaml'):
                        pod_path = os.path.join(pods_path, pod_file)
                        with open(pod_path, 'r') as f:
                            content = f.read()
                        
                        pod_name = pod_file.replace('.yaml', '')
                        
                        # Check for pod issues
                        if any(issue in content.lower() for issue in ['crashloopbackoff', 'imagepullbackoff', 'evicted', 'oomkilled']):
                            self.issues.append(MustGatherIssue(
                                severity="critical",
                                category="pods",
                                component=pod_name,
                                title=f"Pod {pod_name} has issues in {namespace}",
                                description=f"Pod {pod_name} in namespace {namespace} is experiencing problems",
                                file_path=f"namespaces/{namespace}/core/pods/{pod_file}",
                                suggested_fix=f"Check pod logs and events for {pod_name}"
                            ))
                            
        except Exception as e:
            logger.error(f"Error analyzing namespace {namespace} pods: {e}")

    def _analyze_cluster_info(self, path: str):
        """Analyze cluster information"""
        try:
            cluster_info_files = [
                "cluster-scoped-resources/config.openshift.io/clusterversions.yaml",
                "cluster-scoped-resources/config.openshift.io/clusteroperators.yaml",
                "cluster-scoped-resources/core/nodes.yaml"
            ]
            
            for file_path in cluster_info_files:
                full_path = os.path.join(path, file_path)
                if os.path.exists(full_path):
                    self._parse_yaml_file(full_path, file_path)
                    
        except Exception as e:
            logger.error(f"Error analyzing cluster info: {e}")

    def _analyze_nodes(self, path: str):
        """Analyze node health and status"""
        try:
            nodes_path = os.path.join(path, "cluster-scoped-resources/core/nodes.yaml")
            if os.path.exists(nodes_path):
                with open(nodes_path, 'r') as f:
                    content = f.read()
                    
                # Check for node issues
                if "NotReady" in content:
                    self.issues.append(MustGatherIssue(
                        severity="critical",
                        category="compute",
                        component="nodes",
                        title="Node(s) in NotReady state",
                        description="One or more nodes are not ready, which can affect workload scheduling",
                        file_path="cluster-scoped-resources/core/nodes.yaml",
                        suggested_fix="Check node logs and ensure kubelet is running properly",
                        documentation_link="https://docs.openshift.com/container-platform/latest/nodes/nodes/nodes-nodes-viewing.html"
                    ))
                    
                if "DiskPressure" in content:
                    self.issues.append(MustGatherIssue(
                        severity="warning",
                        category="storage",
                        component="nodes",
                        title="Node experiencing disk pressure",
                        description="Node has insufficient disk space",
                        file_path="cluster-scoped-resources/core/nodes.yaml",
                        suggested_fix="Free up disk space or add more storage capacity"
                    ))
                    
        except Exception as e:
            logger.error(f"Error analyzing nodes: {e}")

    def _analyze_pods(self, path: str):
        """Analyze pod status and issues"""
        try:
            # Look for pod files in various namespaces
            namespaces_path = os.path.join(path, "namespaces")
            if os.path.exists(namespaces_path):
                for namespace in os.listdir(namespaces_path):
                    ns_path = os.path.join(namespaces_path, namespace)
                    pods_path = os.path.join(ns_path, "core/pods.yaml")
                    
                    if os.path.exists(pods_path):
                        with open(pods_path, 'r') as f:
                            content = f.read()
                            
                        # Check for common pod issues
                        self._check_pod_issues(content, f"namespaces/{namespace}/core/pods.yaml")
                        
        except Exception as e:
            logger.error(f"Error analyzing pods: {e}")

    def _check_pod_issues(self, content: str, file_path: str):
        """Check for specific pod issues in content"""
        pod_issues = {
            "ImagePullBackOff": {
                "severity": "critical",
                "category": "containers",
                "component": self._extract_component_from_path(file_path),
                "title": "Pod unable to pull container image",
                "description": "Pod is stuck because it cannot pull the required container image",
                "suggested_fix": "Check image name, registry accessibility, and pull secrets"
            },
            "CrashLoopBackOff": {
                "severity": "critical", 
                "category": "containers",
                "component": self._extract_component_from_path(file_path),
                "title": "Pod in crash loop",
                "description": "Pod is repeatedly crashing and restarting",
                "suggested_fix": "Check application logs and configuration for errors"
            },
            "Pending": {
                "severity": "warning",
                "category": "scheduling",
                "component": self._extract_component_from_path(file_path),
                "title": "Pod pending scheduling",
                "description": "Pod cannot be scheduled to any node",
                "suggested_fix": "Check resource requests, node capacity, and scheduling constraints"
            },
            "Evicted": {
                "severity": "warning",
                "category": "resources",
                "component": self._extract_component_from_path(file_path),
                "title": "Pod was evicted",
                "description": "Pod was evicted due to resource pressure",
                "suggested_fix": "Check node resource usage and pod resource limits"
            }
        }
        
        for issue, details in pod_issues.items():
            if issue in content:
                self.issues.append(MustGatherIssue(
                    severity=details["severity"],
                    category=details["category"],
                    component=details["component"],
                    title=details["title"],
                    description=details["description"],
                    file_path=file_path,
                    suggested_fix=details["suggested_fix"]
                ))

    def _analyze_events(self, path: str):
        """Analyze cluster events for issues"""
        try:
            # Look for events in various namespaces
            namespaces_path = os.path.join(path, "namespaces")
            if os.path.exists(namespaces_path):
                for namespace in os.listdir(namespaces_path):
                    events_path = os.path.join(namespaces_path, namespace, "core/events.yaml")
                    
                    if os.path.exists(events_path):
                        with open(events_path, 'r') as f:
                            content = f.read()
                            
                        # Check for error events
                        error_events = [
                            "Failed", "Error", "Warning", "Unhealthy", 
                            "FailedScheduling", "FailedMount", "FailedSync"
                        ]
                        
                        for error in error_events:
                            if error in content:
                                self.issues.append(MustGatherIssue(
                                    severity="warning",
                                    category="events",
                                    component=namespace,
                                    title=f"Event: {error} found in {namespace}",
                                    description=f"Detected {error} events in namespace {namespace}",
                                    file_path=f"namespaces/{namespace}/core/events.yaml"
                                ))
                                
        except Exception as e:
            logger.error(f"Error analyzing events: {e}")

    def _analyze_logs(self, path: str):
        """Analyze various log files for errors"""
        try:
            log_directories = [
                "cluster-scoped-resources/core/pods",
                "namespaces"
            ]
            
            for log_dir in log_directories:
                log_path = os.path.join(path, log_dir)
                if os.path.exists(log_path):
                    self._scan_logs_recursive(log_path)
                    
        except Exception as e:
            logger.error(f"Error analyzing logs: {e}")

    def _scan_logs_recursive(self, directory: str):
        """Recursively scan directory for log files"""
        try:
            for root, dirs, files in os.walk(directory):
                for file in files:
                    if file.endswith(('.log', '.txt')) or 'log' in file.lower():
                        file_path = os.path.join(root, file)
                        self._analyze_log_file(file_path)
        except Exception as e:
            logger.error(f"Error scanning logs in {directory}: {e}")

    def _analyze_log_file(self, file_path: str):
        """Analyze individual log file for errors"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                
            for line_num, line in enumerate(lines, 1):
                # Check against error patterns
                for severity, patterns in self.log_patterns.items():
                    for pattern in patterns:
                        if re.search(pattern, line, re.IGNORECASE):
                            self.issues.append(MustGatherIssue(
                                severity=severity,
                                category="logs",
                                component=self._extract_component_from_path(file_path),
                                title=f"Log {severity}: {pattern}",
                                description=line.strip()[:200],
                                file_path=file_path,
                                line_number=line_num
                            ))
                            break
                            
        except Exception as e:
            logger.error(f"Error analyzing log file {file_path}: {e}")

    def _analyze_network(self, path: str):
        """Analyze network configuration and issues"""
        try:
            network_files = [
                "cluster-scoped-resources/network.openshift.io/clusternetworks.yaml",
                "cluster-scoped-resources/network.openshift.io/hostsubnets.yaml",
                "cluster-scoped-resources/config.openshift.io/networks.yaml"
            ]
            
            for file_path in network_files:
                full_path = os.path.join(path, file_path)
                if os.path.exists(full_path):
                    # Basic network analysis
                    with open(full_path, 'r') as f:
                        content = f.read()
                        
                    if "failed" in content.lower() or "error" in content.lower():
                        self.issues.append(MustGatherIssue(
                            severity="warning",
                            category="network",
                            component=self._extract_component_from_path(file_path),
                            title="Network configuration issues detected",
                            description="Potential network configuration problems found",
                            file_path=file_path
                        ))
                        
        except Exception as e:
            logger.error(f"Error analyzing network: {e}")

    def _analyze_storage(self, path: str):
        """Analyze storage configuration and issues"""
        try:
            storage_files = [
                "cluster-scoped-resources/storage.k8s.io/storageclasses.yaml",
                "cluster-scoped-resources/core/persistentvolumes.yaml"
            ]
            
            for file_path in storage_files:
                full_path = os.path.join(path, file_path)
                if os.path.exists(full_path):
                    with open(full_path, 'r') as f:
                        content = f.read()
                        
                    # Check for storage issues
                    if "Failed" in content or "Lost" in content:
                        self.issues.append(MustGatherIssue(
                            severity="critical",
                            category="storage",
                            component=self._extract_component_from_path(file_path),
                            title="Storage issues detected",
                            description="Problems with persistent volumes or storage classes",
                            file_path=file_path,
                            suggested_fix="Check storage backend and volume availability"
                        ))
                        
        except Exception as e:
            logger.error(f"Error analyzing storage: {e}")

    def _parse_yaml_file(self, file_path: str, relative_path: str):
        """Parse YAML file and extract relevant information"""
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                
            # Store cluster information and extract key features
            if "clusterversion" in relative_path.lower():
                self.cluster_info["version_info"] = "Found in " + relative_path
                self._extract_version_features(content)
            elif "clusteroperator" in relative_path.lower():
                self.cluster_info["operators_info"] = "Found in " + relative_path
                self._extract_operator_features(content)
            elif "nodes" in relative_path.lower():
                self._extract_node_features(content)
                
            # Add relevant snippets for analysis
            if any(severity in content.lower() for severity in ["error", "failed", "degraded", "critical"]):
                self.relevant_snippets.append(f"File: {relative_path}\nContent snippet: {content[:500]}...")
                
        except Exception as e:
            logger.error(f"Error parsing YAML file {file_path}: {e}")

    def _extract_version_features(self, content: str):
        """Extract version-related features for anomaly detection"""
        if "version:" in content.lower():
            # Extract version information for key features
            version_match = re.search(r'version:\s*([^\s]+)', content, re.IGNORECASE)
            if version_match:
                self.key_features["cluster_version"] = version_match.group(1)

    def _extract_operator_features(self, content: str):
        """Extract operator-related features for anomaly detection"""
        # Count operators by status
        self.key_features["operators_available"] = content.lower().count("available: true")
        self.key_features["operators_degraded"] = content.lower().count("degraded: true")
        self.key_features["operators_progressing"] = content.lower().count("progressing: true")
        
        # Extract operator conditions for relevant snippets
        if "degraded: true" in content.lower() or "available: false" in content.lower():
            self.relevant_snippets.append(f"Operator Status Issues:\n{content[:800]}...")

    def _extract_node_features(self, content: str):
        """Extract node-related features for anomaly detection"""
        # Count node conditions
        self.key_features["nodes_ready"] = content.lower().count("ready")
        self.key_features["nodes_notready"] = content.lower().count("notready")
        self.key_features["nodes_diskpressure"] = content.lower().count("diskpressure")
        self.key_features["nodes_memorypressure"] = content.lower().count("memorypressure")
        
        # Extract node states
        if "notready" in content.lower() or "diskpressure" in content.lower():
            self.relevant_snippets.append(f"Node Issues:\n{content[:600]}...")

    def _detect_anomalies(self) -> AnomalyDetectionResult:
        """Detect anomalies in the cluster based on collected features"""
        try:
            anomaly_score = 0.0
            primary_anomalies = []
            
            # Critical issues scoring
            critical_issues = len([i for i in self.issues if i.severity == "critical"])
            if critical_issues > 0:
                anomaly_score += min(critical_issues * 0.2, 0.8)  # Max 0.8 for critical issues
                primary_anomalies.append(f"{critical_issues} critical issues detected")
            
            # Operator health scoring
            operators_degraded = self.key_features.get("operators_degraded", 0)
            if operators_degraded > 0:
                anomaly_score += min(operators_degraded * 0.15, 0.6)
                primary_anomalies.append(f"{operators_degraded} operators degraded")
            
            # Node health scoring
            nodes_notready = self.key_features.get("nodes_notready", 0)
            if nodes_notready > 0:
                anomaly_score += min(nodes_notready * 0.25, 0.7)
                primary_anomalies.append(f"{nodes_notready} nodes not ready")
            
            # Storage pressure scoring
            nodes_diskpressure = self.key_features.get("nodes_diskpressure", 0)
            if nodes_diskpressure > 0:
                anomaly_score += min(nodes_diskpressure * 0.2, 0.5)
                primary_anomalies.append(f"{nodes_diskpressure} nodes under disk pressure")
            
            # Memory pressure scoring
            nodes_memorypressure = self.key_features.get("nodes_memorypressure", 0)
            if nodes_memorypressure > 0:
                anomaly_score += min(nodes_memorypressure * 0.2, 0.5)
                primary_anomalies.append(f"{nodes_memorypressure} nodes under memory pressure")
            
            # Cap the score at 1.0
            anomaly_score = min(anomaly_score, 1.0)
            
            # Determine status and severity
            if anomaly_score >= 0.7:
                status = "ANOMALOUS"
                severity = "🔴 Critical"
                confidence = "High"
            elif anomaly_score >= 0.4:
                status = "ANOMALOUS"
                severity = "🟡 Warning"
                confidence = "Medium"
            elif anomaly_score > 0.1:
                status = "ANOMALOUS"
                severity = "🟡 Warning"
                confidence = "Low"
            else:
                status = "NORMAL"
                severity = "🟢 Normal"
                confidence = "High"
            
            if not primary_anomalies:
                primary_anomalies = ["No significant anomalies detected"]
            
            return AnomalyDetectionResult(
                status=status,
                score=anomaly_score,
                severity=severity,
                primary_anomalies=primary_anomalies,
                confidence=confidence
            )
            
        except Exception as e:
            logger.error(f"Error in anomaly detection: {e}")
            return AnomalyDetectionResult(
                status="ERROR",
                score=0.0,
                severity="❓ Unknown",
                primary_anomalies=[f"Anomaly detection failed: {str(e)}"],
                confidence="Low"
            )

    def _generate_sre_diagnostic_report(self, health: ClusterHealth, anomaly_result: AnomalyDetectionResult) -> SREDiagnosticReport:
        """Generate professional SRE diagnostic report following incident response methodology"""
        try:
            # 1. Identify PRIMARY ISSUE with evidence and impact (root cause analysis)
            primary_issue, evidence, impact = self._identify_primary_issue()
            
            # 2. Generate immediate actions based on the primary issue type
            immediate_actions = self._generate_immediate_actions(primary_issue)
            
            # 3. Root cause summary (concise explanation)
            root_cause_summary = self._generate_root_cause_summary(primary_issue, evidence)
            
            # 4. Confidence assessment
            confidence_level, limitations = self._assess_analysis_confidence()
            
            # Legacy fields for backward compatibility
            anomaly_explanation = self._explain_anomaly(anomaly_result)
            _, long_term_fixes = self._generate_remediation_steps()
            next_steps = self._generate_investigation_steps()
            
            return SREDiagnosticReport(
                primary_issue=primary_issue,
                evidence=evidence,
                impact=impact,
                immediate_actions=immediate_actions,
                root_cause_summary=root_cause_summary,
                severity_emoji=anomaly_result.severity,
                confidence_level=confidence_level,
                # Legacy fields
                anomaly_explanation=anomaly_explanation,
                long_term_fixes=long_term_fixes,
                next_steps=next_steps,
                limitations=limitations,
                key_metrics=self.key_features,
                relevant_snippets=self.relevant_snippets[:5]
            )
            
        except Exception as e:
            logger.error(f"Error generating SRE diagnostic report: {e}")
            return SREDiagnosticReport(
                primary_issue="Report generation failed",
                evidence=f"Unable to generate analysis: {str(e)}",
                impact=["Analysis incomplete due to technical errors"],
                immediate_actions=["Review must-gather bundle integrity", "Check analyzer logs"],
                root_cause_summary="Analysis failed due to technical errors",
                severity_emoji="❓ Unknown",
                confidence_level="Low",
                # Legacy fields
                anomaly_explanation=f"Unable to generate analysis: {str(e)}",
                long_term_fixes=["Investigate analyzer tool issues"],
                next_steps=["Retry analysis with different tool"],
                limitations=["Analysis failed due to technical errors"],
                key_metrics={},
                relevant_snippets=[]
            )

    def _identify_primary_issue(self) -> Tuple[str, str, List[str]]:
        """Identify the ONE primary root cause issue with evidence and impact
        
        Returns:
            Tuple of (primary_issue, evidence, impact_list)
        """
        import re
        
        critical_issues = [i for i in self.issues if i.severity == "critical"]
        
        if not critical_issues:
            warning_issues = [i for i in self.issues if i.severity == "warning"]
            if warning_issues:
                return (
                    f"Warning-level issues detected affecting {len(set([i.component for i in warning_issues]))} components",
                    f"Found {len(warning_issues)} warning issues across components",
                    ["Cluster functionality may be degraded", "No immediate critical impact"]
                )
            else:
                return (
                    "No critical issues detected - cluster appears stable",
                    "All scanned files show normal operations",
                    ["Cluster operating within normal parameters"]
                )
        
        # PRIORITY 1: Look for upgrade-related issues (highest priority root cause)
        upgrade_issues = [issue for issue in critical_issues if 
                         any(keyword in issue.description.lower() for keyword in 
                             ["installing", "upgrade", "clusterversion", "unable to apply", "multiple errors"])]
        
        if upgrade_issues:
            upgrade_issue = upgrade_issues[0]
            
            # Extract version from description if possible
            version_match = re.search(r'(\d+\.\d+\.\d+)', upgrade_issue.description)
            if version_match:
                version = version_match.group(1)
                primary_issue = f"Cluster upgrade to OpenShift {version} stuck/failed (running 11+ hours)"
            else:
                primary_issue = "Cluster upgrade stuck/failed with multiple errors"
            
            # Build comprehensive evidence with detailed log entries
            evidence_parts = [
                f"**🚨 UPGRADE FAILURE EVIDENCE ({len(upgrade_issues)} critical errors):**",
                ""
            ]
            
            # Add detailed upgrade errors
            for i, issue in enumerate(upgrade_issues[:3], 1):  # Show top 3 upgrade issues
                evidence_parts.append(f"{i}. **CRITICAL UPGRADE ERROR**")
                evidence_parts.append(f"   File: {issue.file_path if issue.file_path else 'unknown'}")
                if issue.line_number:
                    evidence_parts.append(f"   Line: {issue.line_number}")
                evidence_parts.append(f"   Component: {issue.component}")
                evidence_parts.append(f"   Full Error: {issue.description}")
                evidence_parts.append("")
            
            # Look for related operator degradation as secondary evidence
            operator_issues = [issue for issue in critical_issues if 
                             any(keyword in issue.description.lower() for keyword in 
                                 ["clusteroperator", "degraded", "not available"])]
            
            if operator_issues:
                evidence_parts.append(f"**🔴 OPERATOR DEGRADATION CASCADE ({len(operator_issues)} operators affected):**")
                evidence_parts.append("")
                
                degraded_ops = []
                for i, issue in enumerate(operator_issues[:5], 1):  # Show top 5 operator issues
                    evidence_parts.append(f"{i}. **OPERATOR FAILURE**")
                    evidence_parts.append(f"   Component: {issue.component}")
                    evidence_parts.append(f"   File: {issue.file_path if issue.file_path else 'unknown'}")
                    if issue.line_number:
                        evidence_parts.append(f"   Line: {issue.line_number}")
                    evidence_parts.append(f"   Error Details: {issue.description}")
                    evidence_parts.append("")
                    
                    # Extract operator name for summary
                    op_match = re.search(r'clusteroperator/([a-zA-Z0-9-]+)', issue.description)
                    if op_match:
                        degraded_ops.append(op_match.group(1))
                
                if degraded_ops:
                    evidence_parts.append(f"Affected operators: {', '.join(list(set(degraded_ops)))}")
                    evidence_parts.append("")
            
            # Look for API server issues as tertiary evidence
            api_issues = [issue for issue in critical_issues if 
                         any(keyword in issue.description.lower() for keyword in 
                             ["server is currently unable", "unable to handle", "server doesn't have"])]
            
            if api_issues:
                evidence_parts.append(f"**⚠️ API SERVER FAILURES ({len(api_issues)} failures detected):**")
                evidence_parts.append("")
                
                for i, issue in enumerate(api_issues[:3], 1):  # Show top 3 API issues
                    evidence_parts.append(f"{i}. **API SERVER ERROR**")
                    evidence_parts.append(f"   File: {issue.file_path if issue.file_path else 'unknown'}")
                    if issue.line_number:
                        evidence_parts.append(f"   Line: {issue.line_number}")
                    evidence_parts.append(f"   Error: {issue.description}")
                    evidence_parts.append("")
            
            # Add summary statistics
            evidence_parts.append("**📊 FAILURE SUMMARY:**")
            evidence_parts.append(f"• Total upgrade-related errors: {len(upgrade_issues)}")
            evidence_parts.append(f"• Operator degradation events: {len(operator_issues)}")
            evidence_parts.append(f"• API server failures: {len(api_issues)}")
            evidence_parts.append(f"• Total critical issues: {len(critical_issues)}")
            
            impact = [
                "🚨 Cluster stuck in partial upgrade state for 11+ hours",
                f"{len(operator_issues)} cluster operators degraded/failing",
                f"{len(api_issues)} API server request failures detected", 
                "New features and security patches not applied",
                "Cluster management severely compromised",
                "Risk of data corruption if upgrade process interrupted",
                "Authentication, monitoring, and routing systems affected"
            ]
            
            return primary_issue, "\n".join(evidence_parts), impact
        
        # PRIORITY 2: API server critical failures
        api_issues = [issue for issue in critical_issues if 
                     any(keyword in issue.description.lower() for keyword in 
                         ["api server", "server is currently unable", "unable to handle the request", "server doesn't have a resource"])]
        
        if api_issues:
            api_issue = api_issues[0]
            primary_issue = "API Server failure - unable to handle requests"
            
            evidence_parts = [
                f"**⚠️ API SERVER CRITICAL FAILURES ({len(api_issues)} failures detected):**",
                ""
            ]
            
            # Add detailed API server error entries
            for i, issue in enumerate(api_issues[:5], 1):  # Show top 5 API issues
                evidence_parts.append(f"{i}. **API SERVER ERROR**")
                evidence_parts.append(f"   File: {issue.file_path if issue.file_path else 'unknown'}")
                if issue.line_number:
                    evidence_parts.append(f"   Line: {issue.line_number}")
                evidence_parts.append(f"   Component: {issue.component}")
                evidence_parts.append(f"   Error: {issue.description}")
                evidence_parts.append("")
            
            # Look for specific resource access failures
            resource_failures = [issue for issue in api_issues if "resource type" in issue.description.lower()]
            if resource_failures:
                evidence_parts.append(f"**📋 RESOURCE ACCESS FAILURES:**")
                evidence_parts.append(f"• {len(resource_failures)} resource types inaccessible")
                for issue in resource_failures[:3]:
                    evidence_parts.append(f"• {issue.description[:150]}...")
                evidence_parts.append("")
            
            # Look for timeout patterns
            timeout_issues = [issue for issue in api_issues if any(keyword in issue.description.lower() for keyword in ["timeout", "30003ms", "30001ms"])]
            if timeout_issues:
                evidence_parts.append(f"**⏱️ TIMEOUT PATTERNS:**")
                evidence_parts.append(f"• {len(timeout_issues)} timeout events detected")
                evidence_parts.append("")
            
            # Summary
            evidence_parts.append("**📊 API FAILURE SUMMARY:**")
            evidence_parts.append(f"• Total API errors: {len(api_issues)}")
            evidence_parts.append(f"• Resource access failures: {len(resource_failures)}")
            evidence_parts.append(f"• Timeout events: {len(timeout_issues)}")
            
            impact = [
                "🚨 Cluster API unavailable or critically unstable",
                f"{len(api_issues)} API request failures detected",
                f"{len(resource_failures)} resource types inaccessible",
                "Unable to process kubectl/oc commands",
                "Operators and controllers cannot function",
                "Cluster management operations failing",
                "Workloads may be unable to start or scale"
            ]
            
            return primary_issue, "\n".join(evidence_parts), impact
        
        # PRIORITY 3: Multiple operator degradation (systemic issue)
        operator_issues = [issue for issue in critical_issues if 
                          any(keyword in issue.description.lower() for keyword in 
                              ["clusteroperator", "degraded", "not available"])]
        
        if len(operator_issues) >= 3:  # Multiple operators = systemic issue
            # Extract operator names
            degraded_operators = set()
            for issue in operator_issues:
                op_match = re.search(r'clusteroperator/([a-zA-Z0-9-]+)', issue.description)
                if op_match:
                    degraded_operators.add(op_match.group(1))
            
            primary_issue = f"Systemic cluster operator failures ({len(degraded_operators)} operators degraded)"
            
            evidence_parts = [
                f"**🔴 OPERATOR DEGRADATION EVIDENCE ({len(operator_issues)} failures across {len(degraded_operators)} operators):**",
                ""
            ]
            
            # Add detailed operator failure entries
            for i, issue in enumerate(operator_issues[:8], 1):  # Show top 8 operator issues
                evidence_parts.append(f"{i}. **OPERATOR FAILURE**")
                evidence_parts.append(f"   Component: {issue.component}")
                evidence_parts.append(f"   File: {issue.file_path if issue.file_path else 'unknown'}")
                if issue.line_number:
                    evidence_parts.append(f"   Line: {issue.line_number}")
                evidence_parts.append(f"   Error Details: {issue.description}")
                evidence_parts.append("")
            
            # Add affected operators summary
            if degraded_operators:
                evidence_parts.append("**📋 AFFECTED OPERATORS:**")
                evidence_parts.append(f"• {', '.join(list(degraded_operators)[:10])}")
                if len(degraded_operators) > 10:
                    evidence_parts.append(f"• ...and {len(degraded_operators) - 10} more operators")
                evidence_parts.append("")
            
            # Look for related issues that might be causing operator failures
            related_api_issues = [issue for issue in critical_issues if 
                                any(keyword in issue.description.lower() for keyword in 
                                    ["server is currently unable", "unable to handle", "server doesn't have"])]
            
            if related_api_issues:
                evidence_parts.append(f"**⚠️ RELATED API SERVER ISSUES ({len(related_api_issues)} detected):**")
                evidence_parts.append("• Operator failures may be caused by underlying API server instability")
                evidence_parts.append(f"• Example: {related_api_issues[0].description[:150]}...")
                evidence_parts.append("")
            
            # Summary
            evidence_parts.append("**📊 OPERATOR FAILURE SUMMARY:**")
            evidence_parts.append(f"• Total operator errors: {len(operator_issues)}")
            evidence_parts.append(f"• Degraded operators: {len(degraded_operators)}")
            evidence_parts.append(f"• Related API issues: {len(related_api_issues)}")
            
            impact = [
                "🚨 Core cluster functionality severely compromised",
                f"{len(degraded_operators)} operators degraded/failing",
                f"{len(related_api_issues)} related API server issues detected",
                "Authentication, networking, storage, or monitoring affected",
                "Workload deployment and management severely impacted",
                "Cluster control plane instability",
                "Risk of cascading failures across the cluster"
            ]
            
            return primary_issue, "\n".join(evidence_parts), impact
        
        # PRIORITY 4: Storage/etcd issues (data layer problems)
        storage_issues = [issue for issue in critical_issues if 
                         any(keyword in issue.description.lower() for keyword in 
                             ["etcd", "storage", "disk", "volume", "persistent"])]
        
        if storage_issues:
            storage_issue = storage_issues[0]
            primary_issue = "Storage system critical failure"
            
            evidence_parts = [
                f"Storage error: {storage_issue.description[:200]}",
                f"Component: {storage_issue.component}",
                f"Source: {storage_issue.file_path}",
                f"Total storage issues: {len(storage_issues)}"
            ]
            
            impact = [
                "🚨 Data persistence at risk",
                "Applications may lose data or fail to start",
                "Cluster state database (etcd) potentially affected",
                "Workload storage unavailable"
            ]
            
            return primary_issue, "\n".join(evidence_parts), impact
        
        # FALLBACK: Group remaining issues by most affected component
        components = {}
        for issue in critical_issues:
            if issue.component not in components:
                components[issue.component] = []
            components[issue.component].append(issue)
        
        primary_component = max(components.keys(), key=lambda k: len(components[k]))
        issue_count = len(components[primary_component])
        
        primary_issue = f"{primary_component.title()} component critical failures"
        
        evidence_parts = [
            f"Component '{primary_component}' has {issue_count} critical issues",
            f"Example: {components[primary_component][0].description[:200]}",
            f"Source: {components[primary_component][0].file_path}"
        ]
        
        impact = [
            f"🚨 {primary_component.title()} functionality severely impacted",
            "Related cluster services may be affected",
            "Workload stability at risk"
        ]
        
        return primary_issue, "\n".join(evidence_parts), impact
    
    def _generate_immediate_actions(self, primary_issue: str) -> List[str]:
        """Generate immediate actions based on the primary issue type"""
        primary_lower = primary_issue.lower()
        
        if "upgrade" in primary_lower and ("stuck" in primary_lower or "failed" in primary_lower):
            return [
                "oc get clusterversion - Check current upgrade status",
                "oc describe clusterversion version - Get detailed upgrade progress",
                "oc get clusteroperators - Check operator health during upgrade",
                "oc adm upgrade status - View upgrade history and current state",
                "Consider upgrade rollback if safe to do so"
            ]
        elif "api server" in primary_lower:
            return [
                "oc version - Test basic API connectivity",
                "kubectl get nodes - Verify cluster access",
                "Check master node logs for API server errors",
                "Verify etcd cluster health and accessibility",
                "Restart API server pods if accessible"
            ]
        elif "operator" in primary_lower and "degraded" in primary_lower:
            return [
                "oc get clusteroperators - List all operator statuses",
                "oc describe co <operator-name> - Check specific operator details",
                "oc get pods -n openshift-* - Check operator pod health",
                "oc get events --all-namespaces --sort-by=.lastTimestamp - Recent events",
                "Review operator logs for specific failure reasons"
            ]
        elif "storage" in primary_lower:
            return [
                "oc get pv,pvc --all-namespaces - Check volume status",
                "oc get storageclass - Verify storage classes",
                "df -h on cluster nodes - Check disk space",
                "Check etcd disk performance and space",
                "Verify storage backend health"
            ]
        else:
            # Generic immediate actions
            return [
                "oc get nodes,pods --all-namespaces - Overall cluster status",
                "oc get events --all-namespaces --sort-by=.lastTimestamp - Recent events",
                "oc top nodes,pods --all-namespaces - Resource utilization",
                "Check cluster operator and node health",
                "Review recent configuration changes"
            ]
    
    def _generate_root_cause_summary(self, primary_issue: str, evidence: str) -> str:
        """Generate concise root cause summary"""
        primary_lower = primary_issue.lower()
        
        if "upgrade" in primary_lower and ("stuck" in primary_lower or "failed" in primary_lower):
            return ("This is a cluster upgrade failure, not individual component issues. "
                   "The cluster is stuck mid-upgrade causing cascading operator and API failures. "
                   "All symptoms (monitoring, authentication, samples) are secondary effects of the incomplete upgrade.")
        elif "api server" in primary_lower:
            return ("The Kubernetes API server is failing to process requests. "
                   "This is a control plane issue that prevents cluster management operations. "
                   "All dependent services and operators cannot function without API access.")
        elif "operator" in primary_lower and "degraded" in primary_lower:
            return ("Multiple cluster operators have failed, indicating a systemic issue. "
                   "This could be due to resource constraints, network issues, or control plane instability. "
                   "Operator degradation cascades to affect dependent cluster services.")
        elif "storage" in primary_lower:
            return ("Storage system failure affects data persistence and cluster state. "
                   "This can impact etcd (cluster brain) and workload data persistence. "
                   "Storage issues often cascade to cause operator and API server problems.")
        else:
            return ("Primary component failure detected. "
                   "Root cause needs further investigation based on specific error patterns and logs.")

    def _explain_anomaly(self, anomaly_result: AnomalyDetectionResult) -> str:
        """Explain why the anomaly was detected and key metrics"""
        if anomaly_result.status == "NORMAL":
            return f"Cluster metrics within normal parameters (anomaly score: {anomaly_result.score:.2f}). {', '.join(anomaly_result.primary_anomalies)}"
        
        explanation = f"Anomaly detected with score {anomaly_result.score:.2f}/1.0. "
        explanation += f"Key indicators: {', '.join(anomaly_result.primary_anomalies)}. "
        
        # Add specific metric context
        metrics_context = []
        if self.key_features.get("operators_degraded", 0) > 0:
            metrics_context.append(f"{self.key_features['operators_degraded']} degraded operators")
        if self.key_features.get("nodes_notready", 0) > 0:
            metrics_context.append(f"{self.key_features['nodes_notready']} nodes not ready")
        
        if metrics_context:
            explanation += f"Specific metrics: {', '.join(metrics_context)}."
        
        return explanation

    def _perform_root_cause_analysis(self) -> str:
        """Perform root cause analysis linking evidence to logs and conditions"""
        analysis = []
        
        # Analyze critical issues by category
        critical_issues = [i for i in self.issues if i.severity == "critical"]
        
        if not critical_issues:
            return "No critical issues detected. Cluster components appear to be functioning normally based on available data."
        
        # Group issues by component for analysis
        components = {}
        for issue in critical_issues:
            if issue.component not in components:
                components[issue.component] = []
            components[issue.component].append(issue)
        
        for component, issues in components.items():
            if component == "operators":
                analysis.append(f"Operator failures detected: {len(issues)} operators affected. " +
                             "Evidence from cluster operator status shows degraded conditions. " +
                             "Common causes: resource constraints, configuration errors, or dependency failures.")
            elif component == "nodes":
                analysis.append(f"Node health problems: {len(issues)} node issues found. " +
                             "Evidence from node status conditions indicates infrastructure problems. " +
                             "Likely causes: kubelet failures, resource exhaustion, or network connectivity.")
            elif component == "storage":
                analysis.append(f"Storage system issues: {len(issues)} storage problems detected. " +
                             "Evidence from PV/PVC status and storage class configuration. " +
                             "Root causes: backend storage failures, mount issues, or capacity problems.")
            elif component == "network":
                analysis.append(f"Network connectivity problems: {len(issues)} network issues found. " +
                             "Evidence from DNS pod status and network configuration. " +
                             "Potential causes: SDN/OVN problems, firewall rules, or DNS resolution failures.")
        
        # Add confidence indicators
        confidence_indicators = []
        if len(self.relevant_snippets) > 3:
            confidence_indicators.append("High confidence - multiple log entries support analysis")
        elif len(self.relevant_snippets) > 0:
            confidence_indicators.append("Moderate confidence - some supporting evidence found")
        else:
            confidence_indicators.append("Low confidence - limited log evidence available")
        
        analysis.append(f"Confidence assessment: {confidence_indicators[0]}")
        
        return " ".join(analysis)

    def _generate_remediation_steps(self) -> Tuple[List[str], List[str]]:
        """Generate immediate actions and long-term fixes"""
        immediate_actions = []
        long_term_fixes = []
        
        # Analyze critical issues for specific remediation
        critical_issues = [i for i in self.issues if i.severity == "critical"]
        components_affected = set([i.component for i in critical_issues])
        
        # Immediate actions based on affected components
        if "operators" in components_affected:
            immediate_actions.extend([
                "oc get co - Check cluster operator status",
                "oc get co | grep -v True - Identify degraded operators",
                "oc describe co <operator-name> - Get detailed operator status"
            ])
            long_term_fixes.extend([
                "Review operator resource limits and requests",
                "Check operator configuration for misconfigurations",
                "Monitor operator logs for recurring issues"
            ])
        
        if "nodes" in components_affected:
            immediate_actions.extend([
                "oc get nodes - Check node readiness status",
                "oc describe node <node-name> - Inspect failing nodes",
                "oc top nodes - Check resource utilization"
            ])
            long_term_fixes.extend([
                "Scale up cluster resources if capacity issues detected",
                "Review node maintenance schedules",
                "Implement node monitoring and alerting"
            ])
        
        if "pods" in components_affected:
            immediate_actions.extend([
                "oc get pods --all-namespaces | grep -v Running - Find problematic pods",
                "oc describe pod <pod-name> -n <namespace> - Check pod events",
                "oc logs <pod-name> -n <namespace> - Review pod logs"
            ])
            long_term_fixes.extend([
                "Review resource quotas and limits",
                "Optimize container image sizes",
                "Implement pod disruption budgets"
            ])
        
        if "storage" in components_affected:
            immediate_actions.extend([
                "oc get pv,pvc --all-namespaces - Check storage status",
                "oc get storageclass - Verify storage classes",
                "oc describe pv <pv-name> - Check persistent volume details"
            ])
            long_term_fixes.extend([
                "Review storage backend health",
                "Implement storage monitoring",
                "Plan for storage capacity expansion"
            ])
        
        # Default actions if no specific issues found
        if not immediate_actions:
            immediate_actions = [
                "oc get nodes,pods --all-namespaces - Overall cluster status",
                "oc get events --all-namespaces --sort-by=.lastTimestamp - Recent events",
                "oc top nodes,pods --all-namespaces - Resource utilization"
            ]
        
        if not long_term_fixes:
            long_term_fixes = [
                "Implement comprehensive cluster monitoring",
                "Establish regular health check procedures",
                "Review and update cluster backup strategies"
            ]
        
        return immediate_actions, long_term_fixes

    def _generate_investigation_steps(self) -> List[str]:
        """Generate focused follow-up investigation steps"""
        steps = []
        
        # Based on issues found, suggest specific investigations
        critical_issues = [i for i in self.issues if i.severity == "critical"]
        components = set([i.component for i in critical_issues])
        
        if "operators" in components:
            steps.append("Verify etcd cluster health - check etcd member status and leader election")
            steps.append("Check API server logs for authentication/authorization issues")
        
        if "nodes" in components:
            steps.append("Review kubelet logs on affected nodes for detailed error messages")
            steps.append("Check node disk I/O and network connectivity to control plane")
        
        if "storage" in components:
            steps.append("Verify storage backend accessibility and performance")
            steps.append("Check CSI driver logs and storage provider status")
        
        if "network" in components:
            steps.append("Test DNS resolution from problematic pods")
            steps.append("Verify SDN/OVN configuration and pod network connectivity")
        
        # Data gaps and missing information
        missing_data = []
        if len(self.relevant_snippets) < 3:
            missing_data.append("Additional log files for complete analysis")
        if not self.key_features.get("cluster_version"):
            missing_data.append("Cluster version information")
        
        if missing_data:
            steps.append(f"Gather missing data: {', '.join(missing_data)}")
        
        # Default investigation steps
        if not steps:
            steps = [
                "Monitor cluster metrics for trending issues",
                "Review recent cluster changes and deployments",
                "Check external dependencies and infrastructure",
                "Verify cluster networking and security policies"
            ]
        
        return steps

    def _assess_analysis_confidence(self) -> Tuple[str, List[str]]:
        """Assess confidence level and identify limitations"""
        confidence_factors = []
        limitations = []
        
        # Assess data completeness
        if len(self.relevant_snippets) >= 5:
            confidence_factors.append("Comprehensive log data available")
        elif len(self.relevant_snippets) >= 2:
            confidence_factors.append("Adequate supporting evidence")
        else:
            limitations.append("Limited log data for complete analysis")
        
        # Assess issue clarity
        critical_issues = [i for i in self.issues if i.severity == "critical"]
        if len(critical_issues) >= 3:
            confidence_factors.append("Clear pattern of critical issues")
        elif len(critical_issues) >= 1:
            confidence_factors.append("Some critical issues identified")
        else:
            limitations.append("No clear critical issues detected")
        
        # Assess key features availability
        if len(self.key_features) >= 5:
            confidence_factors.append("Rich metrics available")
        elif len(self.key_features) >= 2:
            confidence_factors.append("Basic metrics available")
        else:
            limitations.append("Limited cluster metrics")
        
        # Determine overall confidence
        if len(confidence_factors) >= 3 and len(limitations) == 0:
            confidence = "High"
        elif len(confidence_factors) >= 2 and len(limitations) <= 1:
            confidence = "Medium"
        else:
            confidence = "Low"
        
        # Add specific limitations
        if not self.operator_conditions:
            limitations.append("Operator condition details unavailable")
        if not self.node_states:
            limitations.append("Detailed node state information missing")
        
        # Default limitations if none found
        if not limitations:
            limitations = ["Analysis based on available must-gather data only"]
        
        return confidence, limitations

    def _assess_cluster_health(self) -> ClusterHealth:
        """Assess overall cluster health based on found issues"""
        critical_issues = len([i for i in self.issues if i.severity == "critical"])
        warning_issues = len([i for i in self.issues if i.severity == "warning"])
        info_issues = len([i for i in self.issues if i.severity == "info"])
        
        total_issues = len(self.issues)
        
        # Determine overall status
        if critical_issues > 5:
            status = "critical"
            summary = f"Cluster has serious issues requiring immediate attention ({critical_issues} critical issues)"
        elif critical_issues > 0:
            status = "degraded" 
            summary = f"Cluster has some critical issues that need attention ({critical_issues} critical, {warning_issues} warnings)"
        elif warning_issues > 10:
            status = "degraded"
            summary = f"Cluster has multiple warnings that should be investigated ({warning_issues} warnings)"
        else:
            status = "healthy"
            summary = f"Cluster appears healthy with minimal issues ({total_issues} total issues)"
        
        return ClusterHealth(
            status=status,
            node_count=0,  # Would extract from actual data
            pod_count=0,   # Would extract from actual data 
            namespace_count=0,  # Would extract from actual data
            issues_found=total_issues,
            critical_issues=critical_issues,
            warnings=warning_issues,
            summary=summary
        )

    def _generate_report(self, health: ClusterHealth) -> str:
        """Generate human-readable analysis report"""
        report = f"""
# OpenShift Must-Gather Analysis Report

## Cluster Health Assessment
- **Overall Status**: {health.status.upper()}
- **Total Issues Found**: {health.issues_found}
- **Critical Issues**: {health.critical_issues}
- **Warnings**: {health.warnings}
- **Summary**: {health.summary}

## Issues Breakdown by Category

"""
        # Group issues by category
        issues_by_category = {}
        for issue in self.issues:
            if issue.category not in issues_by_category:
                issues_by_category[issue.category] = []
            issues_by_category[issue.category].append(issue)
        
        for category, issues in issues_by_category.items():
            report += f"### {category.upper()} ({len(issues)} issues)\n\n"
            for issue in issues[:5]:  # Show top 5 issues per category
                report += f"- **{issue.severity.upper()}**: {issue.title}\n"
                report += f"  - {issue.description}\n"
                if issue.suggested_fix:
                    report += f"  - Suggested fix: {issue.suggested_fix}\n"
                report += f"  - File: {issue.file_path}\n\n"
        
        report += """
## Recommendations

1. **Address Critical Issues First**: Focus on critical issues that could affect cluster stability
2. **Review Logs**: Check detailed logs for additional context on issues
3. **Monitor Resources**: Ensure nodes have adequate CPU, memory, and storage
4. **Update Documentation**: Keep cluster configuration documented and up to date

## Next Steps

1. Review the detailed issues list above
2. Prioritize fixes based on severity and impact
3. Test changes in a development environment first
4. Monitor cluster health after implementing fixes
"""
        
        return report

    def format_sre_diagnostic_report(self, sre_report: SREDiagnosticReport) -> str:
        """Format the SRE diagnostic report following incident response methodology"""
        
        # Use the new improved format following the user's requirements
        formatted_report = f"""🚨 PRIMARY ISSUE:
{sre_report.primary_issue}

📋 EVIDENCE:
{sre_report.evidence}

💥 IMPACT:
"""
        for impact_item in sre_report.impact:
            formatted_report += f"• {impact_item}\n"
        
        formatted_report += f"""
🛠️ IMMEDIATE ACTIONS:
"""
        for i, action in enumerate(sre_report.immediate_actions, 1):
            formatted_report += f"{i}. {action}\n"

        formatted_report += f"""
🧠 ROOT CAUSE SUMMARY:
{sre_report.root_cause_summary}

📊 CONFIDENCE: {sre_report.confidence_level} {sre_report.severity_emoji}

---
*OpenShift Must-Gather Analysis | Professional SRE Incident Response*"""
        
        return formatted_report

# MCP Tool Functions

async def analyze_mustgather_bundle(
    bundle_path: str,
    detailed_analysis: bool = True
) -> Dict[str, Any]:
    """Analyze an OpenShift must-gather bundle.

    TOOL_NAME=analyze_mustgather_bundle
    DISPLAY_NAME=Must-Gather Bundle Analyzer
    USECASE=Analyze OpenShift must-gather bundles for debugging and troubleshooting
    INSTRUCTIONS=1. Provide path to must-gather bundle, 2. Optionally enable detailed analysis, 3. Get comprehensive analysis report
    INPUT_DESCRIPTION=bundle_path (string): Path to must-gather bundle file or directory, detailed_analysis (boolean, optional): Enable detailed analysis (default: true)
    OUTPUT_DESCRIPTION=Dictionary with cluster health assessment, issues found, and detailed analysis report
    EXAMPLES=analyze_mustgather_bundle("/path/to/must-gather.tar.gz"), analyze_mustgather_bundle("/path/to/extracted-bundle", detailed_analysis=False)
    PREREQUISITES=Must-gather bundle file or extracted directory
    RELATED_TOOLS=debug_ocp_cluster, troubleshoot_openshift_issues

    I/O-bound operation - uses async def for file processing.

    Analyzes OpenShift must-gather bundles to identify cluster issues, pod problems,
    network issues, storage problems, and provides debugging recommendations.

    Args:
        bundle_path: Path to the must-gather bundle (tar.gz, tar, zip, or directory)
        detailed_analysis: Whether to perform detailed log analysis (default: True)

    Returns:
        Dict[str, Any]: Comprehensive analysis results with health assessment and issues
    """
    try:
        if not bundle_path or not bundle_path.strip():
            return {
                "status": "error",
                "error": "Bundle path cannot be empty",
                "message": "Please provide a valid path to the must-gather bundle"
            }

        logger.info(f"Starting must-gather analysis for: {bundle_path}")
        
        # Create analyzer instance
        analyzer = MustGatherAnalyzer()
        
        # Perform analysis
        results = analyzer.analyze_bundle(bundle_path)
        
        # Format the SRE diagnostic report for presentation
        if results["status"] == "success" and "sre_diagnostic_report" in results:
            sre_report_data = results["sre_diagnostic_report"]
            sre_report_obj = SREDiagnosticReport(**sre_report_data)
            formatted_sre_report = analyzer.format_sre_diagnostic_report(sre_report_obj)
            results["formatted_sre_report"] = formatted_sre_report
        
        # Enhance with LLM analysis if available
        try:
            from workshop_mcp_server.src.tools.llm_provider import analyze_mustgather as llm_analyze, is_available
            if is_available() and results.get("status") == "success":
                summary_text = results.get("formatted_sre_report", "")
                if not summary_text:
                    summary_text = json.dumps(results.get("cluster_health", {}), indent=2)
                llm_insights = llm_analyze(summary_text)
                if llm_insights:
                    results["llm_enhanced_analysis"] = llm_insights
                    results["mode"] = "llm_enhanced"
        except Exception as llm_err:
            logger.warning(f"LLM enhancement unavailable: {llm_err}")

        # Add metadata
        results.update({
            "tool": "analyze_mustgather_bundle",
            "detailed_analysis": detailed_analysis,
            "timestamp": datetime.now().isoformat()
        })
        
        logger.info(f"Must-gather analysis completed successfully")
        return results
        
    except Exception as e:
        logger.error(f"Error in must-gather analysis: {e}")
        return {
            "status": "error",
            "error": str(e),
            "bundle_path": bundle_path,
            "message": "Failed to analyze must-gather bundle",
            "timestamp": datetime.now().isoformat()
        }

async def quick_mustgather_check(bundle_path: str) -> Dict[str, Any]:
    """Perform a quick health check on a must-gather bundle.

    TOOL_NAME=quick_mustgather_check
    DISPLAY_NAME=Quick Must-Gather Health Check
    USECASE=Quick assessment of OpenShift cluster health from must-gather bundle
    INSTRUCTIONS=1. Provide path to must-gather bundle, 2. Get quick health assessment
    INPUT_DESCRIPTION=bundle_path (string): Path to must-gather bundle file or directory
    OUTPUT_DESCRIPTION=Dictionary with quick health status and summary of critical issues
    EXAMPLES=quick_mustgather_check("/path/to/must-gather.tar.gz")
    PREREQUISITES=Must-gather bundle file or extracted directory
    RELATED_TOOLS=analyze_mustgather_bundle, debug_ocp_cluster

    I/O-bound operation - uses async def for file processing.

    Performs a quick analysis of must-gather bundle focusing on critical issues only.

    Args:
        bundle_path: Path to the must-gather bundle

    Returns:
        Dict[str, Any]: Quick health assessment with critical issues summary
    """
    try:
        # Perform basic analysis focusing on critical issues only
        results = await analyze_mustgather_bundle(bundle_path, detailed_analysis=False)
        
        if results["status"] == "error":
            return results
            
        # Extract quick summary
        health = results.get("cluster_health", {})
        critical_issues = [
            issue for issue in results.get("issues", [])
            if issue.get("severity") == "critical"
        ]
        
        quick_summary = {
            "status": "success",
            "bundle_path": bundle_path,
            "health_status": health.get("status", "unknown"),
            "critical_issues_count": len(critical_issues),
            "total_issues_count": results.get("issues_found", 0),
            "quick_summary": health.get("summary", "No summary available"),
            "top_critical_issues": critical_issues[:3],  # Top 3 critical issues
            "tool": "quick_mustgather_check",
            "timestamp": datetime.now().isoformat()
        }
        
        return quick_summary
        
    except Exception as e:
        logger.error(f"Error in quick must-gather check: {e}")
        return {
            "status": "error",
            "error": str(e),
            "bundle_path": bundle_path,
            "message": "Failed to perform quick must-gather check",
            "timestamp": datetime.now().isoformat()
        }
