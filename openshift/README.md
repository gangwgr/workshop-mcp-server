# OpenShift/Kubernetes Deployment

Production-ready Kubernetes manifests for deploying your MCP server using **Red Hat UBI** containers and rootless security.

## 📁 **Deployment Files**

- `deployment.yaml` - Main application deployment with security contexts
- `service.yaml` - Internal service for pod communication
- `route.yaml` - External access route (OpenShift) or use Ingress (K8s)
- `configmap.yaml` - Environment configuration management
- `limitrange.yaml` - Resource limits and requests
- `tenant.yaml` - Multi-tenant namespace configuration
- `kustomization.yaml` - Kustomize overlay configuration

## 🚀 **Quick Deployment**

### **OpenShift:**
```bash
# Deploy to current namespace
oc apply -k .

# Or deploy to specific namespace
oc apply -k . -n your-mcp-namespace
```

### **Kubernetes:**
```bash
# Deploy with Kustomize
kubectl apply -k .

# Or deploy individual files
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
# Note: Replace route.yaml with ingress.yaml for standard K8s
```

## 🔧 **Customization Required**

**Before deployment, update these values:**

1. **`deployment.yaml`** - Image and environment:
   ```yaml
   image: your-registry/your-domain-mcp-server:latest
   env:
   - name: MCP_PORT
     value: "4001"  # Use unique port
   ```

2. **`route.yaml`** - External hostname:
   ```yaml
   spec:
     host: your-domain-mcp-server.apps.cluster.com
   ```

3. **`configmap.yaml`** - Application config:
   ```yaml
   data:
     MCP_HOST: "0.0.0.0"
     MCP_PORT: "4001"
     LOG_LEVEL: "INFO"
   ```

## 🛡️ **Security Features**

✅ **Rootless containers** - Non-root user execution
✅ **Red Hat UBI base** - Enterprise security scanning
✅ **Resource limits** - CPU/memory constraints
✅ **Security contexts** - Minimal privileges
✅ **Health checks** - Readiness and liveness probes

## 📊 **Resource Requirements**

- **CPU**: 100m request, 500m limit
- **Memory**: 128Mi request, 512Mi limit
- **Storage**: None required (stateless)

## 🔍 **Monitoring**

```bash
# Check deployment status
oc get deployments
oc get pods
oc get routes

# View logs
oc logs deployment/your-domain-mcp-server

# Port forward for testing
oc port-forward svc/your-domain-mcp-server 4001:4001
```
