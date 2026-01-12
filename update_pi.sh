#!/bin/bash
# ASFO Deployment Script for Raspberry Pi
# This script should be run on the Pi itself to update ASFO

set -e  # Exit on error

echo "======================================"
echo "   ASFO Local Update Script"
echo "======================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

ASFO_DIR="/home/pi/ASFO"

# Check if running as pi user
if [ "$USER" != "pi" ]; then
    echo -e "${YELLOW}Warning: Not running as 'pi' user. Current user: $USER${NC}"
    echo "Adjusting ASFO directory..."
    ASFO_DIR="$HOME/ASFO"
fi

echo -e "${GREEN}[1/4] Checking ASFO installation...${NC}"

if [ ! -d "$ASFO_DIR" ]; then
    echo -e "${RED}ERROR: ASFO directory not found at $ASFO_DIR${NC}"
    exit 1
fi

echo "  ✓ ASFO directory found at $ASFO_DIR"

cd "$ASFO_DIR"

echo ""
echo -e "${GREEN}[2/4] Current version:${NC}"
git describe --tags --always 2>/dev/null || echo "Unable to determine version"

echo ""
echo -e "${GREEN}[3/4] Pulling latest changes...${NC}"

# Fetch and pull
git fetch origin
git pull origin main

if [ $? -eq 0 ]; then
    echo "  ✓ Git pull successful"
else
    echo -e "${RED}  ✗ Git pull failed${NC}"
    exit 1
fi

# Show new version
echo ""
echo "New version:"
git describe --tags --always

echo ""
echo -e "${GREEN}[4/4] Restarting ASFO service...${NC}"

# Check if running as systemd service
if systemctl list-units --full -all | grep -Fq 'asfo.service'; then
    sudo systemctl restart asfo.service
    
    if [ $? -eq 0 ]; then
        echo "  ✓ Service restarted successfully"
        
        # Wait for service to start
        sleep 2
        
        # Check service status
        if systemctl is-active --quiet asfo.service; then
            echo "  ✓ Service is running"
        else
            echo -e "${YELLOW}  ⚠ Service may not be running properly${NC}"
            sudo systemctl status asfo.service --no-pager -l
        fi
    else
        echo -e "${RED}  ✗ Failed to restart service${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}  ⚠ ASFO systemd service not found${NC}"
    echo "  If you're running ASFO manually, please restart it now"
    echo ""
    echo "  To run ASFO manually:"
    echo "    cd $ASFO_DIR"
    echo "    python3 -m ASFO.app"
fi

echo ""
echo "======================================"
echo "   Update Complete!"
echo "======================================"
echo ""
echo "Web UI: http://$(hostname -I | awk '{print $1}'):5000/ui/index.html"
echo "API Docs: http://$(hostname -I | awk '{print $1}'):5000/docs"
echo ""
