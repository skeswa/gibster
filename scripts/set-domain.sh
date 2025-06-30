#!/bin/bash
# Script to update Gibster domain configuration

set -e

if [ $# -eq 0 ]; then
    echo "Usage: $0 <domain>"
    echo "Example: $0 gibster.example.com"
    exit 1
fi

DOMAIN=$1
PATCH_FILE="k8s/overlays/production/deployment-patches.yaml"
KUSTOMIZATION_FILE="k8s/overlays/production/kustomization.yaml"

echo "🔧 Updating domain to: $DOMAIN"

# Check if files exist
if [ ! -f "$PATCH_FILE" ]; then
    echo "❌ Error: $PATCH_FILE not found"
    exit 1
fi

if [ ! -f "$KUSTOMIZATION_FILE" ]; then
    echo "❌ Error: $KUSTOMIZATION_FILE not found"
    exit 1
fi

# Update the domain in the patch file
sed -i.bak "s/gibster\.example\.com/$DOMAIN/g" "$PATCH_FILE"

# Also update www subdomain
sed -i "s/www\.gibster\.example\.com/www.$DOMAIN/g" "$PATCH_FILE"

# Update API URL in kustomization
sed -i.bak "s|api-url=https://gibster\.example\.com|api-url=https://$DOMAIN|g" "$KUSTOMIZATION_FILE"

echo "✅ Domain updated successfully"
echo ""
echo "📝 Next steps:"
echo "1. Ensure DNS A records point to your cluster ingress IP:"
echo "   - $DOMAIN -> <ingress-ip>"
echo "   - www.$DOMAIN -> <ingress-ip>"
echo ""
echo "2. Deploy to production:"
echo "   kubectl apply -k k8s/overlays/production"
echo ""
echo "3. Monitor certificate provisioning:"
echo "   kubectl describe certificate gibster-cert"
echo "   kubectl get events --field-selector involvedObject.name=gibster-cert"
echo ""
echo "The frontend will automatically use https://$DOMAIN as the API URL."