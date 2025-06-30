#!/bin/bash
# Setup script for Kubernetes deployment

set -e

echo "🚀 Gibster Kubernetes Setup"
echo "=========================="

# Check prerequisites
command -v kubectl >/dev/null 2>&1 || { echo "❌ kubectl is required but not installed. Aborting." >&2; exit 1; }

# Function to generate secure key
generate_key() {
    openssl rand -hex 32
}

# Function to generate Fernet key
generate_fernet_key() {
    python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
}

# Check if kubernetes cluster is accessible
if ! kubectl cluster-info >/dev/null 2>&1; then
    echo "❌ Cannot connect to Kubernetes cluster. Please ensure kubectl is configured."
    exit 1
fi

echo "✅ Connected to Kubernetes cluster"

# Prompt for environment
echo ""
echo "Select environment:"
echo "1) Development (local)"
echo "2) Production"
read -p "Enter choice [1-2]: " ENV_CHOICE

case $ENV_CHOICE in
    1)
        ENVIRONMENT="development"
        OVERLAY_PATH="k8s/overlays/development"
        ;;
    2)
        ENVIRONMENT="production"
        OVERLAY_PATH="k8s/overlays/production"
        ;;
    *)
        echo "❌ Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "📋 Setting up $ENVIRONMENT environment"

# For production, generate secrets
if [ "$ENVIRONMENT" = "production" ]; then
    echo ""
    echo "🔐 Generating secure keys..."
    
    # Create secrets.env file
    cat > "$OVERLAY_PATH/secrets.env" << EOF
database-url=postgresql://gibster:$(generate_key)@gibster-postgres:5432/gibster
postgres-password=$(generate_key)
secret-key=$(generate_key)
encryption-key=$(generate_fernet_key)
EOF
    
    echo "✅ Generated secrets.env in $OVERLAY_PATH"
    echo ""
    echo "⚠️  IMPORTANT: Edit $OVERLAY_PATH/secrets.env and update:"
    echo "   - Database password (use the same value in database-url and postgres-password)"
    echo "   - Keep the generated secret-key and encryption-key or replace with your own"
    echo ""
    read -p "Press enter after you've updated the secrets file..."
fi

# Apply configuration
echo ""
echo "🚀 Deploying to Kubernetes..."
kubectl apply -k "$OVERLAY_PATH"

# Wait for deployments
echo ""
echo "⏳ Waiting for deployments to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/gibster-backend
kubectl wait --for=condition=available --timeout=300s deployment/gibster-frontend

# Show status
echo ""
echo "✅ Deployment complete!"
echo ""
echo "📊 Current status:"
kubectl get pods -l app=gibster
echo ""
kubectl get services -l app=gibster
echo ""
kubectl get ingress

# Instructions
echo ""
echo "🎉 Gibster is deployed!"
echo ""
if [ "$ENVIRONMENT" = "development" ]; then
    echo "📝 Next steps:"
    echo "1. Add to /etc/hosts: 127.0.0.1 gibster.local"
    echo "2. Access frontend: http://gibster.local"
    echo "3. Access API: http://gibster.local/api"
else
    echo "📝 Next steps:"
    echo "1. Configure DNS to point to your ingress IP"
    echo "2. Create TLS certificate:"
    echo "   kubectl create secret tls gibster-tls --cert=tls.crt --key=tls.key"
    echo "3. Update ingress host in $OVERLAY_PATH/deployment-patches.yaml"
fi
echo ""
echo "🔍 View logs:"
echo "kubectl logs -l app=gibster,component=backend -f"
echo ""
echo "For more information, see k8s/README.md"