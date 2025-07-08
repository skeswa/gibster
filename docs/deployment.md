# Deployment Guide

This guide covers deploying Gibster to production using Kubernetes and GitHub Actions.

## Overview

Gibster uses automated CI/CD deployment via GitHub Actions to a Kubernetes cluster. The deployment includes:

- FastAPI backend with Celery workers
- Next.js frontend
- PostgreSQL database
- Redis for task queue
- Automated SSL/TLS via ingress

## Prerequisites

- Kubernetes cluster (1.19+)
- kubectl configured
- GitHub repository
- Container registry access (GitHub Container Registry)
- Domain name for production

## GitHub Repository Setup

### 1. Fork/Clone Repository

```bash
git clone <your-repo-url>
cd gibster
```

### 2. Configure GitHub Secrets

Go to Settings → Secrets → Actions and add:

#### Required Secrets

| Secret Name      | Description                  | Example                          |
| ---------------- | ---------------------------- | -------------------------------- |
| `KUBE_CONFIG`    | Base64 encoded kubeconfig    | `cat ~/.kube/config \| base64`   |
| `DATABASE_URL`   | PostgreSQL connection string | `postgresql://user:pass@host/db` |
| `SECRET_KEY`     | JWT signing key              | `openssl rand -hex 32`           |
| `ENCRYPTION_KEY` | Fernet encryption key        | `openssl rand -hex 32`           |
| `REDIS_PASSWORD` | Redis password               | `openssl rand -hex 32`           |

#### Optional Secrets

| Secret Name       | Description             | Default |
| ----------------- | ----------------------- | ------- |
| `GIBNEY_EMAIL`    | Default Gibney email    | None    |
| `GIBNEY_PASSWORD` | Default Gibney password | None    |
| `SENTRY_DSN`      | Error tracking          | None    |

### 3. Configure GitHub Actions

The deployment workflow (`.github/workflows/deploy.yml`) runs on:

- Push to `main` branch
- Pull requests to `main`

## Kubernetes Setup

### 1. Create Namespace

```bash
kubectl create namespace gibster
```

### 2. Manual Deployment (Optional)

#### Development Environment

```bash
# Apply development configuration
kubectl apply -k k8s/overlays/development

# Check deployment
kubectl get pods -n gibster
kubectl get services -n gibster
```

#### Production Environment

```bash
# Create secrets manually (if not using CI/CD)
kubectl create secret generic gibster-secrets \
  --namespace=gibster \
  --from-literal=database-url="$DATABASE_URL" \
  --from-literal=secret-key="$SECRET_KEY" \
  --from-literal=encryption-key="$ENCRYPTION_KEY" \
  --from-literal=redis-password="$REDIS_PASSWORD"

# Apply production configuration
kubectl apply -k k8s/overlays/production
```

## Automated CI/CD Pipeline

### Pipeline Stages

1. **Test Stage**

   - Runs Python tests with pytest
   - Runs frontend tests with Jest
   - Checks code formatting (black, isort)
   - Type checking (mypy, TypeScript)

2. **Build Stage** (on main branch only)

   - Builds Docker images
   - Tags with git SHA and 'latest'
   - Pushes to GitHub Container Registry

3. **Deploy Stage** (on main branch only)
   - Updates Kubernetes secrets
   - Applies manifests with new image tags
   - Monitors rollout status

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

## Production Configuration

### 1. Domain Setup

Update ingress configuration in `k8s/base/ingress.yaml`:

```yaml
spec:
  rules:
    - host: gibster.yourdomain.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: gibster-frontend
                port:
                  number: 80
```

### 2. SSL/TLS Configuration

Using cert-manager (recommended):

```yaml
metadata:
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
    - hosts:
        - gibster.yourdomain.com
      secretName: gibster-tls
```

### 3. Database Configuration

PostgreSQL is deployed as a StatefulSet with:

- Persistent volume for data
- Automated backups (configure separately)
- Connection pooling via PgBouncer (optional)

### 4. Scaling Configuration

#### Horizontal Pod Autoscaling

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: gibster-backend-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: gibster-backend
  minReplicas: 2
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
```

#### Resource Limits

Configure in deployment patches:

```yaml
resources:
  requests:
    memory: "256Mi"
    cpu: "100m"
  limits:
    memory: "512Mi"
    cpu: "500m"
```

## Monitoring

### 1. Application Health

```bash
# Check pod status
kubectl get pods -n gibster

# View pod logs
kubectl logs -n gibster deployment/gibster-backend -f

# Check service endpoints
kubectl get endpoints -n gibster
```

### 2. Health Checks

Backend health endpoint:

```bash
curl https://gibster.yourdomain.com/health
```

### 3. Metrics and Logs

```bash
# Resource usage
kubectl top pods -n gibster

# Recent events
kubectl get events -n gibster --sort-by='.lastTimestamp'

# Describe pod for details
kubectl describe pod <pod-name> -n gibster
```

## Troubleshooting

### Common Issues

#### Pods Not Starting

```bash
# Check pod events
kubectl describe pod <pod-name> -n gibster

# Check logs
kubectl logs <pod-name> -n gibster --previous
```

#### Database Connection Issues

```bash
# Verify secret exists
kubectl get secret gibster-secrets -n gibster

# Test database connection
kubectl exec -it deployment/gibster-backend -n gibster -- python -c "
from sqlalchemy import create_engine
engine = create_engine('$DATABASE_URL')
engine.connect()
print('Connected!')
"
```

#### Image Pull Errors

```bash
# Check image availability
docker pull ghcr.io/<your-org>/gibster-backend:latest

# Verify image pull secrets
kubectl get secrets -n gibster
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

## Backup and Recovery

### Database Backup

```bash
# Manual backup
kubectl exec deployment/postgres -n gibster -- \
  pg_dump -U postgres gibster > backup-$(date +%Y%m%d).sql

# Restore from backup
kubectl exec -i deployment/postgres -n gibster -- \
  psql -U postgres gibster < backup-20240101.sql
```

### Automated Backups

Configure CronJob for automated backups:

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: postgres-backup
spec:
  schedule: "0 2 * * *" # Daily at 2 AM
  jobTemplate:
    spec:
      template:
        spec:
          containers:
            - name: backup
              image: postgres:13
              command: ["/bin/sh", "-c"]
              args:
                - pg_dump -h postgres -U postgres gibster > /backup/gibster-$(date +%Y%m%d).sql
              volumeMounts:
                - name: backup
                  mountPath: /backup
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
```

### 3. RBAC Configuration

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: gibster-role
rules:
  - apiGroups: [""]
    resources: ["pods", "services"]
    verbs: ["get", "list", "watch"]
```

## Maintenance

### Regular Tasks

1. **Update Dependencies**

   ```bash
   # Update container images
   docker pull ghcr.io/<your-org>/gibster-backend:latest
   docker pull ghcr.io/<your-org>/gibster-frontend:latest
   ```

2. **Clean Up Old Resources**

   ```bash
   # Remove old replica sets
   kubectl delete rs -n gibster $(kubectl get rs -n gibster | grep "0  0  0" | awk '{print $1}')
   ```

3. **Monitor Disk Usage**
   ```bash
   # Check PVC usage
   kubectl exec deployment/postgres -n gibster -- df -h /var/lib/postgresql/data
   ```

### Upgrade Procedure

1. **Test in development first**
2. **Create database backup**
3. **Apply new manifests**
4. **Monitor rollout**
5. **Verify functionality**
6. **Rollback if needed**

## Cost Optimization

### Tips for Reducing Costs

1. **Right-size resources**: Monitor actual usage and adjust requests/limits
2. **Use spot instances**: For non-critical workloads
3. **Implement autoscaling**: Scale down during low usage
4. **Optimize images**: Use multi-stage builds, minimize size
5. **Clean up unused resources**: Remove old deployments, PVCs

## Additional Resources

- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [Next.js Deployment](https://nextjs.org/docs/deployment)
