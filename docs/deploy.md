# Gibster Deployment Guide

This guide covers everything you need to deploy Gibster to production using GitHub Actions and Kubernetes.

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [GitHub Repository Setup](#github-repository-setup)
- [CI/CD Pipeline](#cicd-pipeline)
- [Manual Deployment](#manual-deployment)
- [Architecture](#architecture)
- [Monitoring & Troubleshooting](#monitoring--troubleshooting)
- [Scaling](#scaling)
- [Security Considerations](#security-considerations)

## Overview

Gibster uses GitHub Actions for automated testing, building, and deployment to a Kubernetes cluster. The deployment pipeline:

1. Runs tests on every push and pull request
2. Builds and pushes Docker images on merge to main
3. Automatically deploys to Kubernetes with secrets management
4. Monitors rollout status

## Prerequisites

Before deploying Gibster, you need:

1. **A Kubernetes cluster** with:

   - PostgreSQL (CloudNativePG or similar)
   - Redis (for Celery task queue)
   - cert-manager (for TLS certificates)
   - Ingress controller (nginx or similar)

2. **GitHub repository** with Actions enabled

3. **Domain name** configured with DNS pointing to your cluster

4. **Container registry access** (uses GitHub Container Registry by default)

## GitHub Repository Setup

### Required Secrets

Configure these secrets in your GitHub repository (`Settings > Secrets and variables > Actions`):

#### Deployment Secrets

| Secret        | Description                                  | How to Generate                     |
| ------------- | -------------------------------------------- | ----------------------------------- |
| `KUBE_CONFIG` | Base64-encoded kubeconfig for cluster access | `cat ~/.kube/config \| base64 -w 0` |

#### Application Secrets

| Secret           | Description                           | How to Generate                                                                             |
| ---------------- | ------------------------------------- | ------------------------------------------------------------------------------------------- |
| `DATABASE_URL`   | PostgreSQL connection string          | `postgresql://gibster:password@postgres-cluster-rw.database.svc.cluster.local:5432/gibster` |
| `SECRET_KEY`     | JWT signing key (32-byte hex)         | `openssl rand -hex 32`                                                                      |
| `ENCRYPTION_KEY` | Fernet key for encrypting credentials | `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` |
| `REDIS_PASSWORD` | Redis authentication password         | Get from your Redis deployment                                                              |


### How Secrets Work

All production secrets are automatically injected from GitHub repository secrets during deployment:

1. **GitHub Actions reads secrets** from repository settings
2. **Creates/updates Kubernetes secret** (`gibster-secrets`) in the cluster
3. **Deployments reference** the secret for environment variables

Benefits:

- No secrets stored in code or Kubernetes manifests
- Secrets managed entirely through GitHub UI
- Each deployment recreates the secret with latest values
- Changing a secret only requires updating GitHub and re-running the pipeline

## CI/CD Pipeline

The automated pipeline (`.github/workflows/deploy.yml`) consists of three stages:

### 1. Test Stage

**Triggers:** All pushes and pull requests

- Runs backend tests with pytest
- Checks code formatting (black, isort)
- Runs frontend tests and linting
- Type checks TypeScript code

### 2. Build & Push Stage

**Triggers:** Merges to main branch only

- Builds Docker images for backend and frontend
- Pushes to GitHub Container Registry (ghcr.io)
- Tags images with:
  - Commit SHA (e.g., `ghcr.io/your-org/gibster-backend:abc123`)
  - `latest` tag

### 3. Deploy Stage

**Triggers:** Merges to main branch only

1. Creates/updates Kubernetes secrets from GitHub secrets
2. Updates Kubernetes manifests with new image tags
3. Applies changes to production cluster
4. Monitors rollout status

## Manual Deployment

If you need to deploy without CI/CD:

### 1. Build and Push Images

```bash
# Build images
docker build -t ghcr.io/your-org/gibster-backend:latest ./backend
docker build -t ghcr.io/your-org/gibster-frontend:latest ./frontend

# Login to registry
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin

# Push images
docker push ghcr.io/your-org/gibster-backend:latest
docker push ghcr.io/your-org/gibster-frontend:latest
```

### 2. Create Kubernetes Secrets

```bash
# Create namespace if needed
kubectl create namespace gibster

# Create secrets
kubectl create secret generic gibster-secrets \
  --namespace=gibster \
  --from-literal=database-url="postgresql://gibster:password@postgres-cluster-rw.database.svc.cluster.local:5432/gibster" \
  --from-literal=secret-key="$(openssl rand -hex 32)" \
  --from-literal=encryption-key="$(python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")" \
  --from-literal=redis-password="your-redis-password" \
  --dry-run=client -o yaml | kubectl apply -f -
```

### 3. Deploy Application

```bash
# Apply Kubernetes manifests
kubectl apply -k k8s/overlays/production

# Monitor deployment
kubectl rollout status deployment/gibster-backend -n gibster
kubectl rollout status deployment/gibster-frontend -n gibster
kubectl rollout status deployment/gibster-celery -n gibster
```

### 4. Verify Deployment

```bash
# Check pod status
kubectl get pods -n gibster

# View logs
kubectl logs -n gibster -l component=backend -f

# Check ingress
kubectl get ingress -n gibster
```

The application will be available at your configured domain (e.g., https://gibster.sandile.dev).

## Architecture

### Kubernetes Manifest Structure

The Kubernetes manifests use Kustomize for configuration management:

```
k8s/
├── base/                    # Base Kubernetes resources
│   ├── namespace.yaml       # gibster namespace
│   ├── backend-deployment.yaml
│   ├── frontend-deployment.yaml
│   ├── celery-deployment.yaml
│   ├── configmap.yaml
│   └── kustomization.yaml
└── overlays/
    ├── development/         # Local development settings
    │   ├── deployment-patches.yaml
    │   ├── ingress-patch.yaml
    │   ├── secrets.yaml     # Development secrets
    │   └── kustomization.yaml
    └── production/          # Production settings
        ├── deployment-patches.yaml  # Resource limits, replicas
        └── kustomization.yaml
```

#### Base Resources

- **namespace.yaml**: Creates the `gibster` namespace
- **backend-deployment.yaml**: FastAPI backend service
- **frontend-deployment.yaml**: Next.js frontend service
- **celery-deployment.yaml**: Background worker for scraping
- **configmap.yaml**: Shared configuration

#### Development Overlay

- Uses hardcoded development secrets for convenience
- Single replica for all services
- Reduced resource requirements
- No TLS certificates

#### Production Overlay

- Secrets managed via GitHub Actions
- Multiple replicas for high availability
- Production resource limits
- TLS certificates via cert-manager

### Kubernetes Resources

The deployment creates these resources in the `gibster` namespace:

```
gibster/
├── Deployments
│   ├── gibster-backend      # FastAPI application
│   ├── gibster-frontend     # Next.js application
│   └── gibster-celery       # Background worker
├── Services
│   ├── gibster-backend      # ClusterIP service
│   └── gibster-frontend     # ClusterIP service
├── ConfigMap
│   └── gibster-config       # Environment configuration
├── Secret
│   └── gibster-secrets      # Created by CI/CD
└── Ingress
    └── gibster-ingress      # HTTPS routing
```

### Service Integration

#### Database Connection

- **Read-Write:** `postgres-cluster-rw.database.svc.cluster.local:5432`
- **Read-Only:** `postgres-cluster-ro.database.svc.cluster.local:5432`

#### Redis Connection

- **Master:** `redis.redis.svc.cluster.local:6379`
- **Replicas:** `redis-replica.redis.svc.cluster.local:6379`


### TLS/SSL

TLS certificates are automatically provisioned by cert-manager using Let's Encrypt. The ingress is configured for your domain(s).

## Monitoring & Troubleshooting

### Check Deployment Status

```bash
# Overall status
kubectl get all -n gibster

# Detailed pod information
kubectl describe pod -n gibster -l component=backend
```

### View Logs

```bash
# Backend logs
kubectl logs -n gibster -l component=backend -f

# Frontend logs
kubectl logs -n gibster -l component=frontend -f

# Celery worker logs
kubectl logs -n gibster -l component=celery -f

# Previous logs (if pod restarted)
kubectl logs -n gibster -l component=backend --previous
```

### Common Issues

#### Database Connection Failed

```bash
# Test database connectivity
kubectl run -it --rm debug --image=postgres:15 --restart=Never -n gibster -- \
  psql "postgresql://user:pass@postgres-cluster-rw.database.svc.cluster.local:5432/gibster"
```

#### Redis Connection Failed

```bash
# Test Redis connectivity
kubectl run -it --rm debug --image=redis:7 --restart=Never -n gibster -- \
  redis-cli -h redis.redis.svc.cluster.local -a password ping
```

#### Certificate Issues

```bash
# Check certificate status
kubectl describe certificate gibster-cert -n gibster

# Check cert-manager logs
kubectl logs -n cert-manager deployment/cert-manager
```

#### Image Pull Errors

```bash
# Check if images exist
docker pull ghcr.io/your-org/gibster-backend:latest

# Check image pull secrets
kubectl get secrets -n gibster
```

### Health Checks

The backend exposes health endpoints:

```bash
# From inside cluster
kubectl run -it --rm debug --image=busybox --restart=Never -n gibster -- \
  wget -qO- http://gibster-backend:8000/health

# Port forward for local testing
kubectl port-forward -n gibster svc/gibster-backend 8000:8000
curl http://localhost:8000/health
```

### Metrics

The backend exposes Prometheus metrics at `/metrics`:

```bash
kubectl port-forward -n gibster svc/gibster-backend 8000:8000
curl http://localhost:8000/metrics
```

## Scaling

### Horizontal Scaling

```bash
# Scale backend
kubectl scale deployment gibster-backend -n gibster --replicas=3

# Scale celery workers
kubectl scale deployment gibster-celery -n gibster --replicas=5

# Or use HPA (Horizontal Pod Autoscaler)
kubectl autoscale deployment gibster-backend -n gibster \
  --min=2 --max=10 --cpu-percent=80
```

### Resource Adjustments

Edit `k8s/overlays/production/deployment-patches.yaml` to adjust:

- CPU/Memory requests and limits
- Number of replicas
- Environment-specific settings

Example:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: gibster-backend
spec:
  replicas: 3
  template:
    spec:
      containers:
        - name: backend
          resources:
            requests:
              memory: "256Mi"
              cpu: "100m"
            limits:
              memory: "512Mi"
              cpu: "500m"
```

## Security Considerations

### Best Practices

1. **Secrets Management**

   - All secrets stored in GitHub repository secrets
   - Secrets never committed to code
   - Kubernetes secrets created dynamically

2. **Network Security**

   - All external traffic encrypted with TLS
   - Internal traffic uses cluster networking
   - Network policies isolate namespaces

3. **Container Security**

   - Images scanned in CI/CD pipeline
   - Non-root containers
   - Read-only root filesystems where possible

4. **RBAC**
   - Minimal permissions for service accounts
   - Separate namespaces for isolation

### Security Checklist

Before going to production:

- [ ] Generated secure `SECRET_KEY` and `ENCRYPTION_KEY`
- [ ] Set strong database password
- [ ] Configured TLS certificate for ingress
- [ ] Set up GitHub Actions secrets
- [ ] Configured proper resource limits
- [ ] Reviewed network policies
- [ ] Enabled monitoring and alerting
- [ ] Set up backup procedures

## Local Development Deployment

For local Kubernetes development:

```bash
# Apply development configuration
kubectl apply -k k8s/overlays/development

# This uses:
# - Development secrets (hardcoded for convenience)
# - Single replicas
# - Reduced resource requirements
# - No TLS certificates
```

### Quick Kubernetes Commands

```bash
# Apply configurations using Kustomize
kubectl apply -k k8s/overlays/development    # Development
kubectl apply -k k8s/overlays/production     # Production (manual)

# View generated manifests without applying
kubectl kustomize k8s/overlays/development
kubectl kustomize k8s/overlays/production

# Delete all resources
kubectl delete -k k8s/overlays/development
kubectl delete -k k8s/overlays/production
```

The development overlay includes a `secrets.yaml` file with default development credentials.

## Next Steps

After deployment:

1. **Configure monitoring** - Set up dashboards in Grafana
2. **Set up backups** - Configure database backup procedures
3. **Configure alerts** - Set up alerting for critical issues
4. **Load testing** - Test scaling under load
5. **Security audit** - Review security settings

For more information:

- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [cert-manager Documentation](https://cert-manager.io/docs/)
