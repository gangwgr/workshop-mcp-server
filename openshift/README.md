# OpenShift Deployment Guide

This directory contains the minimal Kubernetes manifests needed to deploy the Template MCP Server on Red Hat OpenShift.

## Prerequisites

- Access to an OpenShift cluster
- `oc` CLI tool installed and configured
- Container image built and available

## Quick Deployment

### 1. Build and Push Container Image

```bash
# Build the container image
podman build -t template-mcp-server:latest .

# Tag for your registry (replace with your registry)
podman tag template-mcp-server:latest your-registry.com/template-mcp-server:latest

# Push to registry
podman push your-registry.com/template-mcp-server:latest
```

### 2. Update Image Reference

Edit `deployment.yaml` and update the image reference:

```yaml
spec:
  template:
    spec:
      containers:
      - name: mcp-server
        image: your-registry.com/template-mcp-server:latest
```

### 3. Deploy to OpenShift

```bash
# Create a new project (optional)
oc new-project mcp-server

# Apply all manifests
oc apply -f openshift/

# Or apply individually
oc apply -f openshift/configmap.yaml
oc apply -f openshift/deployment.yaml
oc apply -f openshift/service.yaml
oc apply -f openshift/route.yaml
```

### 4. Verify Deployment

```bash
# Check deployment status
oc get deployments

# Check pods
oc get pods

# Check service
oc get svc

# Check route
oc get route

# Get the external URL
oc get route template-mcp-server -o jsonpath='{.spec.host}'
```

### 5. Test the Deployment

```bash
# Get the route URL
ROUTE_URL=$(oc get route template-mcp-server -o jsonpath='{.spec.host}')

# Test the server
curl https://$ROUTE_URL/
```

## Configuration

### Environment Variables

Customize the server by editing `configmap.yaml`:

```yaml
data:
  SERVER_NAME: "My Custom MCP Server"
  LOG_LEVEL: "DEBUG"
  CUSTOM_API_KEY: "your-secret-key"
```

Apply changes:

```bash
oc apply -f openshift/configmap.yaml
oc rollout restart deployment/template-mcp-server
```

### Resource Limits

Adjust resource requests and limits in `deployment.yaml`:

```yaml
resources:
  requests:
    memory: "256Mi"
    cpu: "200m"
  limits:
    memory: "512Mi"
    cpu: "500m"
```

### Scaling

Scale the deployment:

```bash
# Scale to 3 replicas
oc scale deployment template-mcp-server --replicas=3

# Or edit the deployment
oc edit deployment template-mcp-server
```

## Security

### Service Account (Optional)

Create a custom service account if needed:

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: mcp-server
```

Add to deployment:

```yaml
spec:
  template:
    spec:
      serviceAccountName: mcp-server
```

### Network Policies

Add network policies for additional security:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: mcp-server-netpol
spec:
  podSelector:
    matchLabels:
      app: template-mcp-server
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector: {}
    ports:
    - protocol: TCP
      port: 8000
```

## Troubleshooting

### Check Logs

```bash
# Get pod logs
oc logs deployment/template-mcp-server

# Follow logs
oc logs -f deployment/template-mcp-server

# Get specific pod logs
oc logs <pod-name>
```

### Debug Pod Issues

```bash
# Describe deployment
oc describe deployment template-mcp-server

# Describe pod
oc describe pod <pod-name>

# Get events
oc get events --sort-by=.metadata.creationTimestamp
```

### Common Issues

1. **Image Pull Errors**: Ensure the image is available and accessible
2. **Resource Limits**: Check if pods are being OOMKilled
3. **Route Issues**: Verify route configuration and TLS settings

## Cleanup

Remove all resources:

```bash
# Delete all resources
oc delete -f openshift/

# Or delete individually
oc delete route template-mcp-server
oc delete service template-mcp-server
oc delete deployment template-mcp-server
oc delete configmap mcp-server-config
```

## Files Overview

- `deployment.yaml` - Main application deployment
- `service.yaml` - Service to expose the deployment
- `route.yaml` - OpenShift route for external access
- `configmap.yaml` - Configuration via environment variables
- `README.md` - This deployment guide 