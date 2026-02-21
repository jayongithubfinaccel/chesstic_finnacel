#!/bin/bash

# ═══════════════════════════════════════════════════════════════════════════
# ONE-COMMAND DEPLOYMENT SCRIPT FOR CHESSTIC
# ═══════════════════════════════════════════════════════════════════════════
# This script handles everything:
#   • Push local changes to GitHub
#   • SSH to server and run update
#   • Verify deployment success
#
# Usage: bash quick_deploy.sh [commit_message]
# Example: bash quick_deploy.sh "Added new feature"
# ═══════════════════════════════════════════════════════════════════════════

set -e

# Configuration
SERVER="159.65.140.136"
SERVER_USER="root"
APP_DIR="/var/www/chesstic"
SERVICE_NAME="chesstic"
DOMAIN="https://chesstic.org"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Get commit message
COMMIT_MSG="${1:-Update deployment}"

echo ""
echo -e "${BOLD}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}║       🚀 CHESSTIC ONE-COMMAND DEPLOYMENT SCRIPT 🚀           ║${NC}"
echo -e "${BOLD}╚═══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# ═══════════════════════════════════════════════════════════════════════════
# STEP 1: Local Git Operations
# ═══════════════════════════════════════════════════════════════════════════
echo -e "${BLUE}${BOLD}[1/5] Local Git Operations${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check if there are changes to commit
if [ -n "$(git status --porcelain)" ]; then
    echo -e "${YELLOW}📝 Changes detected, committing...${NC}"
    git add .
    git commit -m "$COMMIT_MSG"
    echo -e "${GREEN}✅ Changes committed${NC}"
else
    echo -e "${GREEN}✅ No local changes to commit${NC}"
fi

# Push to GitHub
echo -e "${YELLOW}📤 Pushing to GitHub...${NC}"
git push origin main
echo -e "${GREEN}✅ Code pushed to GitHub${NC}"
echo ""

# ═══════════════════════════════════════════════════════════════════════════
# STEP 2: Verify Server Connection
# ═══════════════════════════════════════════════════════════════════════════
echo -e "${BLUE}${BOLD}[2/5] Server Connection Check${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo -e "${YELLOW}🔌 Testing connection to ${SERVER}...${NC}"
if ssh -o ConnectTimeout=5 ${SERVER_USER}@${SERVER} "echo 'Connected'" &> /dev/null; then
    echo -e "${GREEN}✅ Server connection successful${NC}"
else
    echo -e "${RED}❌ Cannot connect to server${NC}"
    exit 1
fi
echo ""

# ═══════════════════════════════════════════════════════════════════════════
# STEP 3: Deploy on Server
# ═══════════════════════════════════════════════════════════════════════════
echo -e "${BLUE}${BOLD}[3/5] Deploying on Server${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo -e "${YELLOW}🚀 Running update script on server...${NC}"
ssh ${SERVER_USER}@${SERVER} "cd ${APP_DIR} && bash update.sh"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Server update completed successfully${NC}"
else
    echo -e "${RED}❌ Server update failed${NC}"
    echo -e "${YELLOW}Check server logs: ssh root@${SERVER} 'sudo journalctl -u ${SERVICE_NAME} -n 50'${NC}"
    exit 1
fi
echo ""

# ═══════════════════════════════════════════════════════════════════════════
# STEP 4: Verify Deployment
# ═══════════════════════════════════════════════════════════════════════════
echo -e "${BLUE}${BOLD}[4/5] Deployment Verification${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check service status
echo -e "${YELLOW}🔍 Checking service status...${NC}"
SERVICE_STATUS=$(ssh ${SERVER_USER}@${SERVER} "systemctl is-active ${SERVICE_NAME}")
if [ "$SERVICE_STATUS" = "active" ]; then
    echo -e "${GREEN}✅ Service is running${NC}"
else
    echo -e "${RED}❌ Service is not running (status: $SERVICE_STATUS)${NC}"
    exit 1
fi

# Test website
echo -e "${YELLOW}🌐 Testing website...${NC}"
sleep 3  # Give it a moment to fully start

HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" ${DOMAIN})
if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✅ Website is responding (HTTP $HTTP_CODE)${NC}"
else
    echo -e "${RED}⚠️  Website returned HTTP $HTTP_CODE${NC}"
fi
echo ""

# ═══════════════════════════════════════════════════════════════════════════
# STEP 5: Summary
# ═══════════════════════════════════════════════════════════════════════════
echo -e "${BLUE}${BOLD}[5/5] Deployment Summary${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Get latest commit info
LATEST_COMMIT=$(git log -1 --pretty=format:"%h - %s (%cr)" 2>/dev/null || echo "Unknown")

echo -e "${GREEN}✨ Deployment completed successfully! ✨${NC}"
echo ""
echo "📋 Deployment Details:"
echo "  • Latest Commit: $LATEST_COMMIT"
echo "  • Server: ${SERVER}"
echo "  • Service: ${SERVICE_NAME} (active)"
echo "  • Website: ${DOMAIN}"
echo ""
echo "🔗 Quick Links:"
echo "  • Website: ${DOMAIN}"
echo "  • GitHub: https://github.com/jayongithubfinaccel/chesstic_finnacel"
echo ""
echo "📊 Monitoring Commands:"
echo "  • View logs: ssh root@${SERVER} 'sudo journalctl -u ${SERVICE_NAME} -f'"
echo "  • Check status: ssh root@${SERVER} 'sudo systemctl status ${SERVICE_NAME}'"
echo "  • View backups: ssh root@${SERVER} 'ls -lah /var/www/chesstic_backup_*'"
echo ""
echo -e "${GREEN}🎉 Your changes are now live!${NC}"
echo ""
