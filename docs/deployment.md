# Deployment Guide

This guide covers deploying Gibster to production using Kubernetes and GitHub Actions.

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [GitHub Repository Setup](#github-repository-setup)
- [Automated CI/CD Pipeline](#automated-cicd-pipeline)
- [Manual Deployment](#manual-deployment)
- [Production Configuration](#production-configuration)
- [Architecture](#architecture)
- [Monitoring & Troubleshooting](#monitoring--troubleshooting)
- [Scaling](#scaling)
- [Backup and Recovery](#backup-and-recovery)
- [Security Best Practices](#security-best-practices)
- [Maintenance](#maintenance)
- [Additional Resources](#additional-resources)

## Overview

Gibster uses automated CI/CD deployment via GitHub Actions to a Kubernetes cluster. The deployment includes:

- FastAPI backend with Celery workers
- Next.js frontend
- PostgreSQL database
- Redis for task queue
- Automated SSL/TLS via cert-manager

The deployment pipeline:

1. Runs tests on every push and pull request
2. Builds and pushes Docker images on merge to main
3. Automatically deploys to Kubernetes with secrets management
4. Monitors rollout status

## Prerequisites

- **Kubernetes cluster** (1.19+) with:
  - PostgreSQL (CloudNativePG or similar)
  - Redis (for Celery task queue)
  - cert-manager (for TLS certificates)
  - Ingress controller (nginx or similar)
- **kubectl** configured
- **GitHub repository** with Actions enabled
- **Domain name** with DNS pointing to your cluster
- **Container registry access** (uses GitHub Container Registry by default)

## GitHub Repository Setup

### 1. Fork/Clone Repository

```bash
git clone <your-repo-url>
cd gibster
```

### 2. Configure GitHub Secrets

Go to Settings → Secrets → Actions and add:

#### Required Secrets

| Secret Name         | Description                  | How to Generate                                                                             |
| ------------------- | ---------------------------- | ------------------------------------------------------------------------------------------- |
| `KUBE_CONFIG`       | Base64 encoded kubeconfig    | `cat ~/.kube/config \| base64`                                                              |
| `DATABASE_URL`      | PostgreSQL connection string | `postgresql://user:pass@host/db`                                                            |
| `SECRET_KEY`        | JWT signing key              | `openssl rand -hex 32`                                                                      |
| `ENCRYPTION_KEY`    | Fernet encryption key        | `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` |
| `REDIS_HOST`        | Redis hostname/service       | `redis.redis.svc.cluster.local` (or your Redis service)                                     |
| `REDIS_PORT`        | Redis port number            | `6379` (default Redis port)                                                                 |
| `REDIS_PASSWORD`    | Redis password               | Get from your Redis deployment                                                              |
| `PRODUCTION_DOMAIN` | Your domain name             | `gibster.yourdomain.com`                                                                    |

#### Optional Secrets

| Secret Name       | Description             | Default |
| ----------------- | ----------------------- | ------- |
| `GIBNEY_EMAIL`    | Default Gibney email    | None    |
| `GIBNEY_PASSWORD` | Default Gibney password | None    |
| `SENTRY_DSN`      | Error tracking          | None    |

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

## Automated CI/CD Pipeline

The deployment workflow (`.github/workflows/deploy.yml`) consists of three stages:

### 1. Test Stage

**Triggers:** All pushes and pull requests

- Runs Python tests with pytest and coverage
- Checks code formatting (black, isort)
- Runs frontend tests with Jest
- Type checks (mypy, TypeScript)
- Lints frontend code

### 2. Build & Push Stage

**Triggers:** Merges to main branch only

- Builds Docker images for backend and frontend
- Pushes to GitHub Container Registry (ghcr.io)
- Tags images with:
  - Commit SHA (e.g., `ghcr.io/your-org/gibster-backend:abc123`)
  - `latest` tag

### 3. Deploy Stage

**Triggers:** Merges to main branch only

1. Generates ingress and certificate from templates using `PRODUCTION_DOMAIN`
2. Creates/updates Kubernetes secrets from GitHub secrets
3. Updates Kubernetes manifests with new image tags
4. Applies changes to production cluster
5. Monitors rollout status

### Triggering Deployment

```bash
# Deployment triggered automatically on merge to main
git checkout main
git pull origin main
git merge feature-branch
git push origin main
```

Monitor deployment:

- GitHub Actions: `https://github.com/<your-org>/gibster/actions`
- Kubernetes: `kubectl get pods -n gibster -w`

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

### 2. Create Kubernetes Namespace and Secrets

```bash
# Create namespace if needed
kubectl create namespace gibster

# Create secrets
kubectl create secret generic gibster-secrets \
  --namespace=gibster \
  --from-literal=database-url="$DATABASE_URL" \
  --from-literal=secret-key="$SECRET_KEY" \
  --from-literal=encryption-key="$ENCRYPTION_KEY" \
  --from-literal=redis-host="$REDIS_HOST" \
  --from-literal=redis-port="$REDIS_PORT" \
  --from-literal=redis-password="$REDIS_PASSWORD" \
  --dry-run=client -o yaml | kubectl apply -f -
```

### 3. Generate Domain-Specific Resources

```bash
cd k8s/overlays/production

# Generate ingress from template
export PRODUCTION_DOMAIN="your-domain.com"
sed "s/\${PRODUCTION_DOMAIN}/$PRODUCTION_DOMAIN/g" ingress-template.yaml > ingress.yaml
sed "s/\${PRODUCTION_DOMAIN}/$PRODUCTION_DOMAIN/g" certificate-template.yaml > certificate.yaml

# Update kustomization.yaml to include generated files
cat >> kustomization.yaml << EOF
patchesStrategicMerge:
- ingress.yaml
- certificate.yaml
EOF
```

### 4. Deploy Application

```bash
# Apply Kubernetes manifests
kubectl apply -k k8s/overlays/production

# Monitor deployment
kubectl rollout status deployment/gibster-backend -n gibster
kubectl rollout status deployment/gibster-frontend -n gibster
kubectl rollout status deployment/gibster-celery -n gibster
```

### 5. Verify Deployment

```bash
# Check pod status
kubectl get pods -n gibster

# View logs
kubectl logs -n gibster -l component=backend -f

# Check ingress
kubectl get ingress -n gibster
```

The application will be available at `https://<your-domain>`

## Production Configuration

### 1. Domain Setup

The domain is configured via the `PRODUCTION_DOMAIN` GitHub secret. During deployment, the CI/CD pipeline will:

1. Generate ingress configuration from the template files
2. Replace `${PRODUCTION_DOMAIN}` placeholders with your actual domain
3. Apply the configuration to your cluster

Make sure your DNS is configured to point to your cluster's ingress controller.

### 2. SSL/TLS Configuration

TLS certificates are automatically provisioned by cert-manager using Let's Encrypt. The certificate configuration is generated from templates during deployment and will include:

- Your production domain
- www subdomain (if applicable)
- Automatic renewal before expiration

### 3. Database Configuration

PostgreSQL is deployed as a StatefulSet with:

- Persistent volume for data
- Automated backups (configure separately)
- Connection pooling via PgBouncer (optional)

Connection strings:

- **Read-Write:** `postgres-cluster-rw.database.svc.cluster.local:5432`
- **Read-Only:** `postgres-cluster-ro.database.svc.cluster.local:5432`

### 4. Redis Configuration

Redis connection:

- **Master:** `redis.redis.svc.cluster.local:6379`
- **Replicas:** `redis-replica.redis.svc.cluster.local:6379`

## Architecture

### Kubernetes Manifest Structure

```
k8s/
├── base/                           # Base Kubernetes resources
│   ├── namespace.yaml              # gibster namespace
│   ├── backend-deployment.yaml     # FastAPI backend
│   ├── frontend-deployment.yaml    # Next.js frontend
│   ├── celery-deployment.yaml      # Background worker
│   ├── configmap.yaml              # Shared configuration
│   └── kustomization.yaml
└── overlays/
    ├── development/                # Local development settings
    │   ├── deployment-patches.yaml
    │   ├── secrets.yaml            # Development secrets
    │   └── kustomization.yaml
    └── production/                 # Production settings
        ├── deployment-patches.yaml # Resource limits, replicas
        ├── ingress-template.yaml   # Ingress template
        ├── certificate-template.yaml # Certificate template
        └── kustomization.yaml
```

### Deployed Resources

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
├── Ingress
│   └── gibster-ingress      # HTTPS routing
└── Certificate
    └── gibster-cert         # TLS certificate
```

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

### Health Checks

```bash
# From inside cluster
kubectl run -it --rm debug --image=busybox --restart=Never -n gibster -- \
  wget -qO- http://gibster-backend:8000/health

# Port forward for local testing
kubectl port-forward -n gibster svc/gibster-backend 8000:8000
curl http://localhost:8000/health
```

### Common Issues

#### Database Connection Failed

```bash
# Test database connectivity
kubectl run -it --rm debug --image=postgres:15 --restart=Never -n gibster -- \
  psql "$DATABASE_URL"

# Check secret
kubectl get secret gibster-secrets -n gibster -o yaml
```

#### Redis Connection Failed

```bash
# Test Redis connectivity
kubectl run -it --rm debug --image=redis:7 --restart=Never -n gibster -- \
  redis-cli -h redis.redis.svc.cluster.local -a $REDIS_PASSWORD ping
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

# Check events
kubectl get events -n gibster --sort-by='.lastTimestamp'
```

### Rollback Procedure

```bash
# View rollout history
kubectl rollout history deployment/gibster-backend -n gibster

# Rollback to previous version
kubectl rollout undo deployment/gibster-backend -n gibster

# Rollback to specific revision
kubectl rollout undo deployment/gibster-backend -n gibster --to-revision=2
```

## Scaling

### Horizontal Scaling

```bash
# Scale manually
kubectl scale deployment gibster-backend -n gibster --replicas=3
kubectl scale deployment gibster-celery -n gibster --replicas=5

# Or use HPA (Horizontal Pod Autoscaler)
kubectl autoscale deployment gibster-backend -n gibster \
  --min=2 --max=10 --cpu-percent=80
```

### Resource Adjustments

Edit `k8s/overlays/production/deployment-patches.yaml`:

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
              memory: '256Mi'
              cpu: '100m'
            limits:
              memory: '512Mi'
              cpu: '500m'
```

## Backup and Recovery

### Manual Database Backup

```bash
# Create backup
kubectl exec deployment/postgres -n gibster -- \
  pg_dump -U postgres gibster > backup-$(date +%Y%m%d).sql

# Restore from backup
kubectl exec -i deployment/postgres -n gibster -- \
  psql -U postgres gibster < backup-20240101.sql
```

### Automated Backups

Create a CronJob for automated backups:

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: postgres-backup
  namespace: gibster
spec:
  schedule: '0 2 * * *' # Daily at 2 AM
  jobTemplate:
    spec:
      template:
        spec:
          containers:
            - name: backup
              image: postgres:13
              command: ['/bin/sh', '-c']
              args:
                - pg_dump -h postgres -U postgres gibster > /backup/gibster-$(date +%Y%m%d).sql
              volumeMounts:
                - name: backup
                  mountPath: /backup
          volumes:
            - name: backup
              persistentVolumeClaim:
                claimName: backup-pvc
```

## Security Best Practices

### 1. Secrets Management

- Never commit secrets to repository
- Use Kubernetes secrets for sensitive data
- Rotate keys regularly
- Consider using external secret managers (Vault, AWS Secrets Manager)

### 2. Network Policies

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: gibster-backend-netpol
  namespace: gibster
spec:
  podSelector:
    matchLabels:
      app: gibster
      component: backend
  policyTypes:
    - Ingress
    - Egress
  ingress:
    - from:
        - podSelector:
            matchLabels:
              app: gibster
              component: frontend
  egress:
    - to:
        - namespaceSelector:
            matchLabels:
              name: database
    - to:
        - namespaceSelector:
            matchLabels:
              name: redis
```

### 3. RBAC Configuration

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: gibster-role
  namespace: gibster
rules:
  - apiGroups: ['']
    resources: ['pods', 'services']
    verbs: ['get', 'list', 'watch']
```

### 4. Security Checklist

Before going to production:

- [ ] Generated secure `SECRET_KEY` and `ENCRYPTION_KEY`
- [ ] Set strong database password
- [ ] Configured `PRODUCTION_DOMAIN` secret
- [ ] Set up all GitHub Actions secrets
- [ ] Configured proper resource limits
- [ ] Reviewed network policies
- [ ] Enabled monitoring and alerting
- [ ] Set up backup procedures
- [ ] Configured image scanning in CI/CD

## Maintenance

### Regular Tasks

1. **Update Dependencies**

   ```bash
   # Update container images
   docker pull ghcr.io/your-org/gibster-backend:latest
   docker pull ghcr.io/your-org/gibster-frontend:latest
   ```

2. **Clean Up Old Resources**

   ```bash
   # Remove old replica sets
   kubectl delete rs -n gibster $(kubectl get rs -n gibster | grep "0  0  0" | awk '{print $1}')
   ```

3. **Monitor Resource Usage**

   ```bash
   # Check resource usage
   kubectl top pods -n gibster

   # Check PVC usage
   kubectl exec deployment/postgres -n gibster -- df -h /var/lib/postgresql/data
   ```

### Upgrade Procedure

1. Test in development environment first
2. Create database backup
3. Review changelog and migration notes
4. Apply new manifests
5. Monitor rollout
6. Verify functionality
7. Rollback if needed

### Cost Optimization

- **Right-size resources**: Monitor actual usage and adjust requests/limits
- **Use spot instances**: For non-critical workloads
- **Implement autoscaling**: Scale down during low usage
- **Optimize images**: Use multi-stage builds, minimize size
- **Clean up unused resources**: Remove old deployments, PVCs

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
kubectl apply -k k8s/overlays/production     # Production

# View generated manifests without applying
kubectl kustomize k8s/overlays/development
kubectl kustomize k8s/overlays/production

# Delete all resources
kubectl delete -k k8s/overlays/development
kubectl delete -k k8s/overlays/production
```

## Additional Resources

- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [cert-manager Documentation](https://cert-manager.io/docs/)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [Next.js Deployment](https://nextjs.org/docs/deployment)
