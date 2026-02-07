# Kubernetes Deployment

This directory contains Kubernetes manifests for deploying EnodAI.

## Structure

```
k8s/
├── base/                    # Base Kubernetes resources
│   ├── namespace.yaml
│   ├── configmap.yaml
│   ├── secret.yaml
│   ├── collector-deployment.yaml
│   ├── ai-service-deployment.yaml
│   ├── postgresql-statefulset.yaml
│   └── ingress.yaml
└── overlays/               # Environment-specific overrides
    ├── dev/
    └── prod/
```

## Prerequisites

- Kubernetes cluster (v1.24+)
- kubectl configured
- Helm (optional, for easier management)
- Ingress controller (nginx)
- Cert-manager (for TLS certificates)

## Deployment

### Using kubectl

```bash
# Create namespace
kubectl apply -f base/namespace.yaml

# Apply base resources
kubectl apply -f base/

# Check deployment status
kubectl get pods -n enodai
```

### Using Kustomize

```bash
# Development environment
kubectl apply -k overlays/dev/

# Production environment
kubectl apply -k overlays/prod/
```

## Scaling

### Manual Scaling

```bash
# Scale collector
kubectl scale deployment collector -n enodai --replicas=5

# Scale AI service
kubectl scale deployment ai-service -n enodai --replicas=3
```

### Auto-scaling

HorizontalPodAutoscalers are automatically configured:
- Collector: 2-10 replicas (70% CPU, 80% Memory)
- AI Service: 2-5 replicas (70% CPU, 80% Memory)

## Monitoring

```bash
# View logs
kubectl logs -f -n enodai deployment/collector
kubectl logs -f -n enodai deployment/ai-service

# Port-forward for local access
kubectl port-forward -n enodai svc/collector 8080:8080
kubectl port-forward -n enodai svc/ai-service 8082:8082
kubectl port-forward -n enodai svc/grafana 3000:3000

# Check resource usage
kubectl top pods -n enodai
```

## Secrets Management

⚠️ **Important**: The provided secrets are for development only.

For production, use one of:
1. Kubernetes Secrets (encrypted at rest)
2. External secrets management (HashiCorp Vault, AWS Secrets Manager)
3. Sealed Secrets

Example with kubectl:
```bash
kubectl create secret generic enodai-secrets \
  --from-literal=POSTGRES_PASSWORD=<strong-password> \
  --from-literal=JWT_SECRET_KEY=<random-key> \
  -n enodai
```

## Persistence

PostgreSQL uses StatefulSet with PersistentVolumeClaims:
- Default: 10Gi per instance
- StorageClass: default (customize as needed)

## Ingress & TLS

1. Install cert-manager:
```bash
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml
```

2. Create ClusterIssuer:
```yaml
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@example.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
```

3. Update ingress.yaml with your domain

## Troubleshooting

### Pods not starting
```bash
kubectl describe pod <pod-name> -n enodai
kubectl logs <pod-name> -n enodai
```

### Service not accessible
```bash
kubectl get svc -n enodai
kubectl get endpoints -n enodai
```

### Database connection issues
```bash
kubectl exec -it postgresql-0 -n enodai -- psql -U kam_user -d kam_alerts
```

## Cleanup

```bash
# Delete all resources
kubectl delete namespace enodai

# Or delete specific resources
kubectl delete -f base/
```
