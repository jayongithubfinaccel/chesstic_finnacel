#!/bin/bash

# Quick update script - use this after initial deployment
# for pulling latest code changes without full redeployment
# Usage: cd /var/www/chesstic && sudo bash update.sh

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🔄 Updating Chesstic application...${NC}"

# Navigate to app directory
cd /var/www/chesstic

# Stash any local changes (shouldn't be any, but just in case)
echo -e "${YELLOW}📦 Checking for local changes...${NC}"
if [ -n "$(git status --porcelain)" ]; then
    echo "Stashing local changes..."
    git stash
fi

# Pull latest code
echo -e "${YELLOW}📥 Pulling latest code from GitHub...${NC}"
git pull origin main

# Install/update Python dependencies
echo -e "${YELLOW}📦 Updating dependencies...${NC}"
source venv/bin/activate
pip install -r requirements.txt --quiet

# Restart service
echo -e "${YELLOW}🔄 Restarting application...${NC}"
systemctl restart chesstic

# Check status
echo -e "${YELLOW}✅ Checking service status...${NC}"
sleep 2
if systemctl is-active --quiet chesstic; then
    echo -e "${GREEN}✅ Chesstic is running!${NC}"
    systemctl status chesstic --no-pager --lines=0
else
    echo -e "${RED}❌ Chesstic failed to start${NC}"
    systemctl status chesstic --no-pager
    exit 1
fi

echo ""
echo -e "${GREEN}════════════════════════════════${NC}"
echo -e "${GREEN}✅ Update completed successfully!${NC}"
echo -e "${GREEN}════════════════════════════════${NC}"
echo ""
echo "Your application is live at:"
echo "• http://159.65.140.136"
echo "• http://chesstic.org (once DNS propagates)"
echo ""
