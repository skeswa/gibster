# Rhuidean Cluster - Deployment Reference for Open Source Projects

This document describes the infrastructure setup and deployment patterns for the **Rhuidean** K3s cluster, designed to help open source projects understand how to deploy applications in a production-ready Kubernetes environment with comprehensive infrastructure services.

## 🏗️ Infrastructure Overview

The Rhuidean cluster provides a complete application platform with integrated services for data storage, caching, monitoring, and security. All services are deployed using industry-standard tools and follow cloud-native best practices.

### Core Infrastructure Services

| Service Category | Technology | Purpose | Integration Pattern |
|------------------|------------|---------|-------------------|
| **Container Platform** | K3s (Kubernetes) | Application orchestration | Standard Kubernetes manifests |
| **Database** | PostgreSQL (CloudNativePG) | Primary data storage | Connection strings via secrets |
| **Object Storage** | MinIO (S3-compatible) | File storage, backups | S3 SDK integration |
| **Caching** | Redis (Master-Replica) | Session storage, caching | Redis client libraries |
| **Monitoring** | Prometheus + Grafana | Observability & alerting | Metrics endpoints |
| **TLS Management** | cert-manager + Let's Encrypt | Automatic SSL certificates | Kubernetes certificates |

## 🎯 Application Deployment Pattern

### 1. **Namespace-Based Isolation**
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: your-application
  labels:
    app.kubernetes.io/name: your-application
    environment: production
```

### 2. **Service Integration via Environment Variables**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: your-app
  namespace: your-application
spec:
  template:
    spec:
      containers:
      - name: app
        image: your-org/your-app:latest
        env:
        # Database connection
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: database-credentials
              key: connection-url
        
        # Redis caching
        - name: REDIS_HOST
          value: "redis.redis.svc.cluster.local"
        - name: REDIS_PASSWORD
          valueFrom:
            secretKeyRef:
              name: redis-credentials
              key: password
        
        # S3-compatible object storage
        - name: S3_ENDPOINT
          value: "http://minio.minio.svc.cluster.local:9000"
        - name: S3_ACCESS_KEY
          valueFrom:
            secretKeyRef:
              name: s3-credentials
              key: access-key
        - name: S3_SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: s3-credentials
              key: secret-key
```

### 3. **External Access with TLS**
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: your-app-ingress
  namespace: your-application
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  tls:
  - hosts:
    - your-app.example.com
    secretName: your-app-tls
  rules:
  - host: your-app.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: your-app-service
            port:
              number: 80
```

## 🔗 Service Discovery Patterns

### Internal Service Communication
All cluster services are accessible via Kubernetes DNS:
```
<service-name>.<namespace>.svc.cluster.local:<port>
```

### Key Service Endpoints
```bash
# Database (read-write)
postgresql://user:pass@postgres-cluster-rw.database.svc.cluster.local:5432/dbname

# Database (read-only replicas) 
postgresql://user:pass@postgres-cluster-ro.database.svc.cluster.local:5432/dbname

# Redis (master for read/write)
redis.cache.svc.cluster.local:6379

# Redis (replicas for read-only)
redis-replica.cache.svc.cluster.local:6379

# S3-compatible object storage
http://minio.storage.svc.cluster.local:9000
```

## 📊 Monitoring Integration

### Application Metrics
Expose metrics for Prometheus scraping:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: your-app-service
  namespace: your-application
  annotations:
    prometheus.io/scrape: "true"
    prometheus.io/port: "8080"
    prometheus.io/path: "/metrics"
spec:
  ports:
  - name: http
    port: 80
    targetPort: 8080
  - name: metrics
    port: 9090
    targetPort: 9090
  selector:
    app: your-app
```

### Custom ServiceMonitor
For advanced metrics collection:

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: your-app-monitor
  namespace: your-application
spec:
  selector:
    matchLabels:
      app: your-app
  endpoints:
  - port: metrics
    interval: 30s
    path: /metrics
```

## 🗄️ Data Storage Patterns

### Database Integration
```python
# Python example with SQLAlchemy
import os
from sqlalchemy import create_engine

DATABASE_URL = os.getenv('DATABASE_URL')
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
```

```javascript
// Node.js example with pg
const { Pool } = require('pg');

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: process.env.NODE_ENV === 'production'
});
```

### Object Storage Integration
```python
# Python with boto3 (S3-compatible)
import boto3
import os

s3_client = boto3.client(
    's3',
    endpoint_url=os.getenv('S3_ENDPOINT'),
    aws_access_key_id=os.getenv('S3_ACCESS_KEY'),
    aws_secret_access_key=os.getenv('S3_SECRET_KEY')
)
```

### Caching Integration
```python
# Python with redis-py
import redis
import os

r = redis.Redis(
    host=os.getenv('REDIS_HOST'),
    port=int(os.getenv('REDIS_PORT', 6379)),
    password=os.getenv('REDIS_PASSWORD'),
    decode_responses=True
)
```

## 🔐 Security & Secrets Management

### Secret Creation Pattern
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: your-app-secrets
  namespace: your-application
type: Opaque
stringData:
  database-url: "postgresql://user:pass@host:5432/dbname"
  api-key: "your-api-key-here"
  session-secret: "your-session-secret"
```

### RBAC for Application
```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: your-application
  name: your-app-role
rules:
- apiGroups: [""]
  resources: ["secrets", "configmaps"]
  verbs: ["get", "list"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: your-app-rolebinding
  namespace: your-application
subjects:
- kind: ServiceAccount
  name: your-app-serviceaccount
  namespace: your-application
roleRef:
  kind: Role
  name: your-app-role
  apiGroup: rbac.authorization.k8s.io
```

## 🚀 Deployment Strategies

### Rolling Updates
```yaml
spec:
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  replicas: 3
```

### Health Checks
```yaml
spec:
  template:
    spec:
      containers:
      - name: app
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
```

### Resource Management
```yaml
spec:
  template:
    spec:
      containers:
      - name: app
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
```

## 📦 Helm Chart Integration

### Chart Structure for Platform Integration
```yaml
# values.yaml
global:
  platform:
    database:
      host: "postgres-cluster-rw.database.svc.cluster.local"
      port: 5432
    redis:
      host: "redis.cache.svc.cluster.local"
      port: 6379
    storage:
      endpoint: "http://minio.storage.svc.cluster.local:9000"

app:
  image:
    repository: your-org/your-app
    tag: "latest"
  
  ingress:
    enabled: true
    annotations:
      cert-manager.io/cluster-issuer: "letsencrypt-prod"
```

## 🔧 CI/CD Integration

### GitOps Deployment Pattern
```yaml
# .github/workflows/deploy.yml
name: Deploy to Rhuidean Cluster
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Configure kubectl
      run: |
        echo "${{ secrets.KUBECONFIG }}" | base64 -d > kubeconfig
        export KUBECONFIG=kubeconfig
    
    - name: Deploy application
      run: |
        kubectl apply -f k8s/namespace.yaml
        kubectl apply -f k8s/secrets.yaml
        kubectl apply -f k8s/deployment.yaml
        kubectl apply -f k8s/service.yaml
        kubectl apply -f k8s/ingress.yaml
    
    - name: Wait for deployment
      run: |
        kubectl rollout status deployment/your-app -n your-application
```

## 🏛️ Architecture Benefits

### High Availability
- **Database**: 3-node PostgreSQL cluster with automatic failover
- **Caching**: Master-replica Redis setup with read scaling
- **Storage**: Distributed object storage with replication
- **Applications**: Multi-replica deployments with load balancing

### Scalability
- **Horizontal scaling**: Add more application replicas
- **Database scaling**: Read replicas for query scaling
- **Storage scaling**: S3-compatible with unlimited capacity
- **Cache scaling**: Redis read replicas for cache scaling

### Security
- **TLS everywhere**: Automatic certificate management
- **Secret management**: Kubernetes-native secret handling
- **Network isolation**: Namespace-based segmentation
- **RBAC**: Fine-grained access control

### Observability
- **Metrics**: Prometheus metrics collection
- **Dashboards**: Grafana visualization
- **Logging**: Centralized log aggregation
- **Alerting**: Proactive issue detection

## 📋 Quick Start Checklist

For deploying a new application to the Rhuidean cluster:

- [ ] **Create namespace** for your application
- [ ] **Create secrets** for database, Redis, and S3 credentials
- [ ] **Configure deployment** with proper resource limits and health checks
- [ ] **Set up service** with appropriate ports and selectors
- [ ] **Configure ingress** with TLS certificate management
- [ ] **Add monitoring** with Prometheus metrics endpoints
- [ ] **Test connectivity** to all infrastructure services
- [ ] **Verify TLS** certificate provisioning
- [ ] **Check logs** and metrics in Grafana
- [ ] **Set up CI/CD** for automated deployments

## 🔗 Integration Libraries

### Recommended client libraries for infrastructure services:

**Database (PostgreSQL):**
- Python: `psycopg2`, `SQLAlchemy`
- Node.js: `pg`, `Sequelize`
- Go: `lib/pq`, `GORM`
- Java: `PostgreSQL JDBC`

**Object Storage (S3-compatible):**
- Python: `boto3`
- Node.js: `aws-sdk`
- Go: `minio-go`
- Java: `AWS SDK for Java`

**Caching (Redis):**
- Python: `redis-py`
- Node.js: `ioredis`
- Go: `go-redis`
- Java: `Jedis`

---

This deployment guide provides the foundation for building cloud-native applications on the Rhuidean cluster infrastructure. The platform handles the complexity of data storage, caching, monitoring, and security, allowing development teams to focus on application logic and user experience.

**Platform Version**: K3s 1.28+  
**Last Updated**: 2024  
**Cluster**: Rhuidean Production Environment 