#!/usr/bin/env bash
# Configure Moonraker for ASFO updates and CORS
set -e

if [ "$EUID" -ne 0 ]; then 
  echo "❌ Please run as root (use sudo)"
  exit 1
fi

INSTALL_DIR="/opt/ASFO"
REPO_URL="https://github.com/alex006l/ASFO.git"
BRANCH="main"
VENV_DIR="$INSTALL_DIR/venv"
MOONRAKER_CONF="/home/pi/printer_data/config/moonraker.conf"

if [ ! -f "$MOONRAKER_CONF" ]; then
  echo "❌ Moonraker config not found at $MOONRAKER_CONF"
  exit 1
fi

echo "🔧 Configuring Moonraker..."

# Get local IP address
LOCAL_IP=$(hostname -I | awk '{print $1}')
echo "Local IP detected: $LOCAL_IP"

# Backup original config
cp "$MOONRAKER_CONF" "${MOONRAKER_CONF}.backup.$(date +%s)"
echo "✅ Backup created: ${MOONRAKER_CONF}.backup.$(date +%s)"

# Add CORS domain if not already present
if ! grep -q "cors_domains:" "$MOONRAKER_CONF"; then
  echo "Adding cors_domains section..."
  cat >> "$MOONRAKER_CONF" << EOF

[server]
cors_domains:
    http://${LOCAL_IP}
    http://${LOCAL_IP}:*
EOF
else
  # Check if our IP is already in cors_domains
  if ! grep -A 10 "cors_domains:" "$MOONRAKER_CONF" | grep -q "$LOCAL_IP"; then
    echo "Adding ${LOCAL_IP} to existing cors_domains..."
    # Insert after cors_domains: line
    sed -i "/cors_domains:/a\\    http://${LOCAL_IP}\n    http://${LOCAL_IP}:*" "$MOONRAKER_CONF"
  else
    echo "✅ CORS domain ${LOCAL_IP} already configured"
  fi
fi

# Add update manager section if not already present
if ! grep -q "\[update_manager ASFO\]" "$MOONRAKER_CONF"; then
  echo "Adding ASFO update manager configuration..."
  cat >> "$MOONRAKER_CONF" << EOF

[update_manager ASFO]
type: git_repo
path: $INSTALL_DIR
origin: $REPO_URL
primary_branch: $BRANCH
managed_services: ASFO
virtualenv: $VENV_DIR
requirements: requirements.txt
install_script: scripts/install_update.sh
EOF
  echo "✅ Update manager configured"
else
  echo "✅ Update manager already configured"
fi

# Restart Moonraker to apply changes
if systemctl is-active --quiet moonraker; then
  echo "🔄 Restarting Moonraker..."
  systemctl restart moonraker
  sleep 3
  
  if systemctl is-active --quiet moonraker; then
    echo "✅ Moonraker restarted successfully"
  else
    echo "⚠️  Moonraker failed to restart. Check logs:"
    echo "   sudo journalctl -u moonraker -n 20"
  fi
else
  echo "⚠️  Moonraker is not running"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Moonraker configuration complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Changes made:"
echo "  • Added CORS domain: http://${LOCAL_IP}"
echo "  • Added ASFO to update manager"
echo "  • Backup saved: ${MOONRAKER_CONF}.backup.*"
echo ""
echo "Next steps:"
echo "  1. Go to Mainsail UI (should load without remote mode warning)"
echo "  2. Navigate to Machine → Update Manager"
echo "  3. You should see 'ASFO' in the list"
echo ""
