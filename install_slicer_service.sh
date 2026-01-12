#!/usr/bin/env bash
set -euo pipefail

# One-line install for Slicing Service on Raspberry Pi
# Usage: curl -fsSL https://raw.githubusercontent.com/YOUR_USERNAME/slicer-service/main/install_slicer_service.sh | sudo bash
#    or: wget -O - https://raw.githubusercontent.com/YOUR_USERNAME/slicer-service/main/install_slicer_service.sh | sudo bash

REPO_URL=${REPO_URL:-"https://github.com/YOUR_USERNAME/slicer-service.git"}
BRANCH=${BRANCH:-"main"}
INSTALL_DIR=/opt/slicer_service
VENV_DIR=$INSTALL_DIR/venv
CURAENGINE_DIR=/opt/CuraEngine
SERVICE_USER=slicer
DATA_DIR=/var/lib/slicer_service
GD=$DATA_DIR/gcodes

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Slicer Service Installer for Raspberry Pi"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
  echo "❌ Please run as root (use sudo)"
  exit 1
fi

echo "📦 Updating package lists..."
apt-get update -qq

echo "📦 Installing build & runtime dependencies..."
apt-get install -y -qq build-essential cmake git python3-venv python3-pip python3-dev \
  libboost-all-dev libeigen3-dev pkg-config curl wget jq

# Create service user
if ! id -u $SERVICE_USER >/dev/null 2>&1; then
  echo "👤 Creating service user: $SERVICE_USER"
  useradd --system --no-create-home --shell /usr/sbin/nologin $SERVICE_USER || true
fi

# Build CuraEngine
if [ -f "/usr/local/bin/CuraEngine" ]; then
  echo "✅ CuraEngine already installed"
else
  echo "🔨 Building CuraEngine (this may take 10-20 minutes)..."
  if [ ! -d "$CURAENGINE_DIR" ]; then
    git clone --depth 1 https://github.com/Ultimaker/CuraEngine.git $CURAENGINE_DIR
  fi
  
  mkdir -p $CURAENGINE_DIR/build
  cd $CURAENGINE_DIR/build
  cmake .. -DCMAKE_BUILD_TYPE=Release
  make -j$(nproc)
  install -m 0755 CuraEngine /usr/local/bin/CuraEngine
  cd -
  echo "✅ CuraEngine installed to /usr/local/bin/CuraEngine"
fi

# Clone or update the slicer service repo
echo "📥 Downloading slicer service..."
if [ -d "$INSTALL_DIR/.git" ]; then
  echo "Updating existing installation..."
  cd $INSTALL_DIR
  git pull origin $BRANCH
else
  rm -rf $INSTALL_DIR
  git closystemd service file
echo "⚙️  Creating systemd service..."
SERVICE_FILE=/etc/systemd/system/slicer_service.service
cat > $SERVICE_FILE <<EOF
[Unit]
Description=Slicer Service (CuraEngine + FastAPI)
After=network.target

[Service]
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$INSTALL_DIR
Environment="PATH=$VENV_DIR/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin"
Environment="DATA_DIR=$DATA_DIR"
Environment="CURAENGINE_PATH=/usr/local/bin/CuraEngine"
ExecStart=$VENV_DIR/bin/uvicorn slicer_service.app:app --host 0.0.0.0 --port 8080 --workers 1
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable slicer_service.service

# Start the service
echo "🚀 Starting slicer service..."
systemctl start slicer_service.service

# Wait a moment and check status
sleep 2
if systemctl is-active --quiet slicer_service.service; then
  echo ""
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "✅ Installation complete!"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo ""
  echo "Service is running at: http://$(hostname -I | awk '{print $1}'):8080"
  echo ""
  echo "Useful commands:"
  echo "  • Check status:  sudo systemctl status slicer_service"
  echo "  • View logs:     sudo journalctl -u slicer_service -f"
  echo "  • Restart:       sudo systemctl restart slicer_service"
  echo "  • Stop:          sudo systemctl stop slicer_service"
  echo ""
  echo "Next steps:"
  echo "  1. Test API: curl http://localhost:8080/"
  echo "  2. Configure Mainsail (see MAINSAIL_INTEGRATION.md)"
  echo "  3. Upload an STL and test slicing"
  echo ""
else
  echo ""
  echo "⚠️  Service failed to start. Check logs:"
  echo "  sudo journalctl -u slicer_service -n 50"
  exit 1
fi
ExecStart=/opt/slicer_service/venv/bin/uvicorn slicer_service.app:app --host 0.0.0.0 --port 8080 --workers 1
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable slicer_service.service || true

echo "Install complete. Next steps:"
echo "- Place your FastAPI app at $INSTALL_DIR (example module: slicer_service.app:app)."
echo "- Start service: sudo systemctl start slicer_service.service"
echo "- Logs: sudo journalctl -u slicer_service.service -f"

echo "Tip: The script built CuraEngine to /usr/local/bin/CuraEngine. Verify with CuraEngine --help."

exit 0
