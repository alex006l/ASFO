#!/usr/bin/env bash
# Configure Mainsail UI to add ASFO integration
set -e

if [ "$EUID" -ne 0 ]; then 
  echo "❌ Please run as root (use sudo)"
  exit 1
fi

MOONRAKER_CONF="/home/pi/printer_data/config/moonraker.conf"
LOCAL_IP=$(hostname -I | awk '{print $1}')

if [ ! -f "$MOONRAKER_CONF" ]; then
  echo "❌ Moonraker config not found"
  exit 1
fi

echo "🎨 Configuring Mainsail UI for ASFO..."

# Add ASFO as a custom webcam/iframe integration
if ! grep -q "\[webcam asfo\]" "$MOONRAKER_CONF"; then
  cat >> "$MOONRAKER_CONF" << EOF

# ASFO Slicer Interface
[webcam asfo]
location: printer
enabled: True
service: iframe
target_fps: 15
stream_url: http://${LOCAL_IP}:8080/ui/
icon: mdi-cube-outline
EOF
  echo "✅ Added ASFO to Mainsail"
else
  echo "✅ ASFO already configured in Mainsail"
fi

# Restart Moonraker
if systemctl is-active --quiet moonraker; then
  echo "🔄 Restarting Moonraker..."
  systemctl restart moonraker
  sleep 3
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Mainsail UI configuration complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "ASFO is now available in Mainsail:"
echo "  • Look for the webcam/camera icon in the top menu"
echo "  • Or go to: http://${LOCAL_IP}:8080/ui/"
echo ""
