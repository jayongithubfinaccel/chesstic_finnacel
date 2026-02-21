#!/bin/bash

# Safe Update Script for Chesstic Production
# Usage: cd /var/www/chesstic && sudo bash update.sh
# This script safely updates your application with automatic rollback

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

APP_DIR="/var/www/chesstic"
SERVICE_NAME="chesstic"

echo -e "${GREEN}🔄 Updating Chesstic application...${NC}"
echo ""

# Navigate to app directory
cd ${APP_DIR}

# Create backup before updating
BACKUP_DIR="${APP_DIR}_backup_$(date +%Y%m%d_%H%M%S)"
echo -e "${YELLOW}📦 Creating backup...${NC}"
cp -r ${APP_DIR} ${BACKUP_DIR}
echo -e "${GREEN}✓ Backup created: ${BACKUP_DIR}${NC}"

# Stash any local changes
echo -e "${YELLOW}📦 Checking for local changes...${NC}"
if [ -n "$(git status --porcelain)" ]; then
    echo "Stashing local changes..."
    git stash
fi

# Pull latest code
echo -e "${YELLOW}📥 Pulling latest code from GitHub...${NC}"
git pull origin main
echo -e "${GREEN}✓ Code updated${NC}"

# Update Python dependencies safely
echo -e "${YELLOW}📦 Updating dependencies (this may take a minute)...${NC}"
source venv/bin/activate
pip install --upgrade pip --quiet
pip install -r requirements.txt --upgrade
echo -e "${GREEN}✓ Dependencies updated${NC}"

# Verify critical packages are installed
echo -e "${YELLOW}🔍 Verifying critical packages...${NC}"
MISSING_PACKAGES=""
for pkg in openai python-chess pytz Flask Flask-CORS requests; do
    if ! pip show $pkg &> /dev/null; then
        MISSING_PACKAGES="$MISSING_PACKAGES $pkg"
    fi
done

if [ ! -z "$MISSING_PACKAGES" ]; then
    echo -e "${RED}✗ Missing packages:$MISSING_PACKAGES${NC}"
    echo -e "${RED}Rolling back...${NC}"
    deactivate
    systemctl stop ${SERVICE_NAME}
    rm -rf ${APP_DIR}
    cp -r ${BACKUP_DIR} ${APP_DIR}
    systemctl start ${SERVICE_NAME}
    exit 1
fi
echo -e "${GREEN}✓ All packages verified${NC}"

deactivate

# Fix permissions
echo -e "${YELLOW}🔒 Fixing permissions...${NC}"
chown -R www-data:www-data ${APP_DIR}
echo -e "${GREEN}✓ Permissions set${NC}"

# Restart service
echo -e "${YELLOW}🔄 Restarting application...${NC}"
systemctl restart ${SERVICE_NAME}
sleep 3

# Check status
echo -e "${YELLOW}✅ Verifying service status...${NC}"
if systemctl is-active --quiet ${SERVICE_NAME}; then
    echo -e "${GREEN}✓ Service is running${NC}"
else
    echo -e "${RED}✗ Service failed to start!${NC}"
    echo -e "${RED}Rolling back to backup...${NC}"
    systemctl stop ${SERVICE_NAME}
    rm -rf ${APP_DIR}
    cp -r ${BACKUP_DIR} ${APP_DIR}
    systemctl start ${SERVICE_NAME}
    echo -e "${RED}✗ Update failed - rolled back to previous version${NC}"
    echo "Check logs: sudo journalctl -u ${SERVICE_NAME} -n 50"
    exit 1
fi

# Test application endpoint
echo -e "${YELLOW}🌐 Testing application endpoint...${NC}"
sleep 2
if curl -f -s http://localhost:8000/ > /dev/null; then
    echo -e "${GREEN}✓ Application responding correctly${NC}"
else
    echo -e "${RED}✗ Application not responding!${NC}"
    echo -e "${RED}Rolling back to backup...${NC}"
    systemctl stop ${SERVICE_NAME}
    rm -rf ${APP_DIR}
    cp -r ${BACKUP_DIR} ${APP_DIR}
    chown -R www-data:www-data ${APP_DIR}
    systemctl start ${SERVICE_NAME}
    echo -e "${RED}✗ Update failed - rolled back to previous version${NC}"
    exit 1
fi

# Clean up old backups (keep last 5)
echo -e "${YELLOW}🧹 Cleaning old backups...${NC}"
ls -dt /var/www/chesstic_backup_* 2>/dev/null | tail -n +6 | xargs rm -rf 2>/dev/null || true
echo -e "${GREEN}✓ Old backups cleaned${NC}"

echo ""
echo -e "${GREEN}✨ Update completed successfully! ✨${NC}"
echo -e "${GREEN}Backup saved at: ${BACKUP_DIR}${NC}"
echo ""
echo "Website: https://chesstic.org"
echo "Service status: sudo systemctl status ${SERVICE_NAME}"
echo "View logs: sudo journalctl -u ${SERVICE_NAME} -f"
echo ""
echo -e "${YELLOW}Note: Backup will be kept. To manually rollback:${NC}"
echo "  sudo systemctl stop ${SERVICE_NAME}"
echo "  sudo rm -rf ${APP_DIR}"
echo "  sudo cp -r ${BACKUP_DIR} ${APP_DIR}"
echo "  sudo systemctl start ${SERVICE_NAME}"

echo ""
echo -e "${GREEN}════════════════════════════════${NC}"
echo -e "${GREEN}✅ Update completed successfully!${NC}"
echo -e "${GREEN}════════════════════════════════${NC}"
echo ""
echo "Your application is live at:"
echo "• http://159.65.140.136"
echo "• http://chesstic.org (once DNS propagates)"
echo ""
