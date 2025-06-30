# Gibster Kubernetes Deployment

This directory contains Kubernetes manifests for deploying Gibster to the Rhuidean cluster.

## Architecture

Gibster is deployed in the `gibster` namespace and integrates with the following Rhuidean cluster services:

- **PostgreSQL**: Primary database (CloudNativePG cluster)
- **Redis**: Caching and task queue (Master-Replica setup)
- **MinIO**: S3-compatible object storage (for future file uploads)
- **cert-manager**: Automatic TLS certificates via Let's Encrypt
- **Prometheus/Grafana**: Monitoring and observability

## Directory Structure

```
k8s/
├── base/                    # Base Kubernetes resources
│   ├── namespace.yaml       # gibster namespace
│   ├── backend-deployment.yaml
│   ├── frontend-deployment.yaml
│   ├── celery-deployment.yaml
│   ├── configmap.yaml
│   ├── secrets.yaml         # Template for secrets
│   └── kustomization.yaml
└── overlays/
    ├── development/         # Local development settings
    └── production/          # Production settings
        ├── deployment-patches.yaml  # Resource limits, replicas
        └── kustomization.yaml
```

## Quick Start

### Prerequisites

1. Access to the Rhuidean cluster with kubectl configured
2. Database credentials from cluster admin
3. Redis password from cluster admin
4. S3 credentials from cluster admin (if using file uploads)

### Local Development

```bash
# Apply development configuration
kubectl apply -k k8s/overlays/development
```

### Production Deployment

Production deployment is automated via GitHub Actions when pushing to the main branch.

Required GitHub Secrets:
- `KUBE_CONFIG`: Base64 encoded kubeconfig for cluster access
- `DATABASE_URL`: PostgreSQL connection string
- `SECRET_KEY`: JWT signing key
- `ENCRYPTION_KEY`: Fernet encryption key for credentials
- `REDIS_PASSWORD`: Redis authentication password
- `S3_ACCESS_KEY`: MinIO access key (optional)
- `S3_SECRET_KEY`: MinIO secret key (optional)

Manual deployment:
```bash
# Create secrets file
cat > k8s/overlays/production/secrets.env << EOF
database-url=postgresql://gibster:password@postgres-cluster-rw.database.svc.cluster.local:5432/gibster
secret-key=$(openssl rand -hex 32)
encryption-key=$(python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
redis-password=your-redis-password
s3-access-key=your-s3-access-key
s3-secret-key=your-s3-secret-key
EOF

# Apply production configuration
kubectl apply -k k8s/overlays/production
```

## Service Integration

### Database Connection

The application connects to the Rhuidean PostgreSQL cluster:
- Read-Write: `postgres-cluster-rw.database.svc.cluster.local:5432`
- Read-Only: `postgres-cluster-ro.database.svc.cluster.local:5432`

### Redis Connection

Redis is used for Celery task queue:
- Master: `redis.redis.svc.cluster.local:6379`
- Replicas: `redis-replica.redis.svc.cluster.local:6379`

### Object Storage (Future)

MinIO S3-compatible storage for file uploads:
- Endpoint: `http://minio.minio.svc.cluster.local:9000`

## Monitoring

The backend service exposes Prometheus metrics at `/metrics` on port 8000.

View metrics in Grafana:
1. Access Grafana dashboard
2. Import the Gibster dashboard (if available)
3. Or create custom queries for `gibster_*` metrics

## TLS/SSL

TLS certificates are automatically provisioned by cert-manager using Let's Encrypt.

The ingress is configured for:
- `gibster.sandile.dev`
- `www.gibster.sandile.dev`

## Troubleshooting

### Check deployment status
```bash
kubectl get all -n gibster
```

### View logs
```bash
# Backend logs
kubectl logs -n gibster -l component=backend -f

# Frontend logs
kubectl logs -n gibster -l component=frontend -f

# Celery worker logs
kubectl logs -n gibster -l component=celery -f
```

### Check certificate status
```bash
kubectl describe certificate gibster-cert -n gibster
```

### Database connection issues
```bash
# Test database connectivity
kubectl run -it --rm debug --image=postgres:15 --restart=Never -n gibster -- \
  psql "postgresql://user:pass@postgres-cluster-rw.database.svc.cluster.local:5432/gibster"
```

### Redis connection issues
```bash
# Test Redis connectivity
kubectl run -it --rm debug --image=redis:7 --restart=Never -n gibster -- \
  redis-cli -h redis.redis.svc.cluster.local -a password ping
```

## Scaling

### Horizontal scaling
```bash
# Scale backend
kubectl scale deployment gibster-backend -n gibster --replicas=5

# Scale celery workers
kubectl scale deployment gibster-celery -n gibster --replicas=5
```

### Resource adjustments

Edit `k8s/overlays/production/deployment-patches.yaml` to adjust:
- CPU/Memory requests and limits
- Number of replicas
- Other deployment parameters

## Security Considerations

1. **Secrets Management**: All sensitive data stored in Kubernetes secrets
2. **Network Policies**: Traffic isolated to gibster namespace
3. **TLS Everywhere**: All external traffic encrypted
4. **RBAC**: Minimal permissions for service accounts
5. **Image Security**: Images scanned in CI/CD pipeline

## CI/CD Pipeline

The GitHub Actions workflow:
1. Runs tests (backend + frontend)
2. Builds Docker images
3. Pushes to GitHub Container Registry
4. Updates Kubernetes manifests with new image tags
5. Applies changes to the cluster

See `.github/workflows/deploy.yml` for details.