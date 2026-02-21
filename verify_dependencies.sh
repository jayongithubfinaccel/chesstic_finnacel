#!/bin/bash

# Dependency Verification Script
# Compares server's installed packages with requirements.txt
# Usage: bash verify_dependencies.sh [server_ip]

SERVER="${1:-159.65.140.136}"
APP_DIR="/var/www/chesstic"

echo "🔍 Verifying dependencies on server ${SERVER}..."
echo ""

# Create temporary file for server packages
TEMP_SERVER_PACKAGES=$(mktemp)
TEMP_REQUIREMENTS=$(mktemp)

# Get installed packages from server
echo "📦 Fetching installed packages from server..."
ssh root@${SERVER} "cd ${APP_DIR} && source venv/bin/activate && pip freeze" > ${TEMP_SERVER_PACKAGES}

if [ $? -ne 0 ]; then
    echo "❌ Failed to connect to server or fetch packages"
    rm -f ${TEMP_SERVER_PACKAGES} ${TEMP_REQUIREMENTS}
    exit 1
fi

# Get requirements.txt (normalize format)
cat requirements.txt | grep -v '^#' | grep -v '^$' > ${TEMP_REQUIREMENTS}

echo "✅ Packages fetched successfully"
echo ""

# Parse and compare
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 DEPENDENCY CHECK REPORT"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

MISSING_PACKAGES=()
VERSION_MISMATCH=()
ALL_GOOD=true

# Check each requirement
while IFS= read -r req; do
    # Skip empty lines and comments
    [[ -z "$req" || "$req" =~ ^# ]] && continue
    
    # Extract package name and version
    PACKAGE_NAME=$(echo "$req" | cut -d'=' -f1 | cut -d'>' -f1 | cut -d'<' -f1 | tr -d ' ')
    REQUIRED_VERSION=$(echo "$req" | grep -oP '==\K[^=]+' || echo "")
    
    # Check if package is installed
    INSTALLED_LINE=$(grep -i "^${PACKAGE_NAME}==" ${TEMP_SERVER_PACKAGES} || echo "")
    
    if [ -z "$INSTALLED_LINE" ]; then
        MISSING_PACKAGES+=("$PACKAGE_NAME")
        echo "❌ MISSING: $PACKAGE_NAME"
        ALL_GOOD=false
    else
        INSTALLED_VERSION=$(echo "$INSTALLED_LINE" | cut -d'=' -f3)
        
        if [ -n "$REQUIRED_VERSION" ] && [ "$INSTALLED_VERSION" != "$REQUIRED_VERSION" ]; then
            VERSION_MISMATCH+=("$PACKAGE_NAME (required: $REQUIRED_VERSION, installed: $INSTALLED_VERSION)")
            echo "⚠️  VERSION MISMATCH: $PACKAGE_NAME"
            echo "   Required: $REQUIRED_VERSION"
            echo "   Installed: $INSTALLED_VERSION"
            ALL_GOOD=false
        else
            echo "✅ OK: $PACKAGE_NAME ($INSTALLED_VERSION)"
        fi
    fi
done < ${TEMP_REQUIREMENTS}

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Summary
echo ""
if [ "$ALL_GOOD" = true ]; then
    echo "🎉 All dependencies are correctly installed!"
else
    echo "⚠️  ISSUES FOUND:"
    
    if [ ${#MISSING_PACKAGES[@]} -gt 0 ]; then
        echo ""
        echo "Missing packages:"
        printf '  - %s\n' "${MISSING_PACKAGES[@]}"
    fi
    
    if [ ${#VERSION_MISMATCH[@]} -gt 0 ]; then
        echo ""
        echo "Version mismatches:"
        printf '  - %s\n' "${VERSION_MISMATCH[@]}"
    fi
    
    echo ""
    echo "🔧 To fix, run on server:"
    echo "   cd ${APP_DIR}"
    echo "   source venv/bin/activate"
    echo "   pip install -r requirements.txt --upgrade"
    echo "   sudo systemctl restart chesstic"
fi

echo ""

# Additional server packages check
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 EXTRA PACKAGES ON SERVER (not in requirements.txt)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

EXTRA_COUNT=0
while IFS= read -r installed; do
    PACKAGE_NAME=$(echo "$installed" | cut -d'=' -f1)
    
    # Skip pip, setuptools, wheel - these are standard
    [[ "$PACKAGE_NAME" =~ ^(pip|setuptools|wheel)$ ]] && continue
    
    # Check if in requirements
    if ! grep -qi "^${PACKAGE_NAME}[=><!]" ${TEMP_REQUIREMENTS}; then
        echo "  $installed"
        ((EXTRA_COUNT++))
    fi
done < ${TEMP_SERVER_PACKAGES}

if [ $EXTRA_COUNT -eq 0 ]; then
    echo "  None (clean environment)"
fi

echo ""

# Cleanup
rm -f ${TEMP_SERVER_PACKAGES} ${TEMP_REQUIREMENTS}

if [ "$ALL_GOOD" = true ]; then
    exit 0
else
    exit 1
fi
