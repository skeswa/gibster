# Gibster Kubernetes Manifests

This directory contains Kubernetes manifests for deploying Gibster using Kustomize.

## Documentation

For comprehensive deployment instructions, see [**../docs/deploy.md**](../docs/deploy.md).

## Quick Reference

```bash
# Development deployment
kubectl apply -k k8s/overlays/development

# Production deployment (via CI/CD)
git push origin main

# Manual production deployment
kubectl apply -k k8s/overlays/production
```

## Directory Structure

- `base/` - Base Kubernetes resources
- `overlays/development/` - Development environment configuration
- `overlays/production/` - Production environment configuration
