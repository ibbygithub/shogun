#!/bin/bash
# Deploy shogun-web to svcnode-01
# Run from: laptop (devops-agent persona)
# Usage: bash app-services/shogun-web/deploy.sh

set -e

SSH="ssh -i ~/.ssh/devops-agent_ed25519_clean devops-agent@192.168.71.220"
BRANCH="${1:-feature/20260313-shogun-web}"

echo "==> Pulling branch $BRANCH on svcnode-01..."
$SSH "cd /opt/git/work/shogun && git fetch origin && git checkout $BRANCH && git pull origin $BRANCH"

echo "==> Building and starting shogun-web-api..."
$SSH "cd /opt/git/work/shogun && docker-compose -f app-services/shogun-web/shogun-web-api/docker-compose.yml up -d --build"

echo "==> Building and starting shogun-web-ui..."
$SSH "cd /opt/git/work/shogun && docker-compose -f app-services/shogun-web/shogun-web-ui/docker-compose.yml up -d --build"

echo "==> Waiting 5s for containers to start..."
sleep 5

echo "==> Health check: API"
$SSH "curl -sf http://localhost:8090/health && echo ' OK' || echo ' FAILED'"

echo "==> Health check: UI"
$SSH "curl -sf http://localhost:3000 -o /dev/null && echo ' OK' || echo ' FAILED'"

echo ""
echo "Deploy complete."
echo "  UI:  http://shogun.ibbytech.com"
echo "  API: http://shogun-api.ibbytech.com/health"
