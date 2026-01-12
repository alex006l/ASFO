#!/usr/bin/env bash
set -euo pipefail

# One-line install for ASFO Slicer Service on Raspberry Pi
# Usage: curl -fsSL https://raw.githubusercontent.com/alex006l/ASFO/main/install_ASFO.sh | sudo bash
#    or: wget -O - https://raw.githubusercontent.com/alex006l/ASFO/main/install_ASFO.sh | sudo bash

REPO_URL=${REPO_URL:-"https://github.com/alex006l/ASFO.git"}
BRANCH=${BRANCH:-"main"}
INSTALL_DIR=/opt/ASFO
VENV_DIR=$INSTALL_DIR/venv
CURAENGINE_DIR=/opt/CuraEngine
SERVICE_USER=asfo
DATA_DIR=/var/lib/ASFO
GCODE_DIR=$DATA_DIR/gcodes
STL_DIR=$DATA_DIR/stls

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ASFO Slicer Service Installer for Raspberry Pi"
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
  libboost-all-dev libeigen3-dev pkg-config curl wget jq python3-setuptools

# Create service user
if ! id -u $SERVICE_USER >/dev/null 2>&1; then
  echo "👤 Creating service user: $SERVICE_USER"
  useradd --system --no-create-home --shell /usr/sbin/nologin $SERVICE_USER || true
fi

# Install CuraEngine
if command -v CuraEngine &> /dev/null || [ -f "/usr/local/bin/CuraEngine" ]; then
  echo "✅ CuraEngine already installed"
else
  echo "🔨 Installing CuraEngine from Debian repository..."
  
  # Install cura-engine package from Debian repos
  if ! apt-get install -y cura-engine; then
    echo "❌ Failed to install CuraEngine package"
    exit 1
  fi
  
  # Verify installation
  if ! command -v CuraEngine &> /dev/null; then
    echo "❌ CuraEngine not found after installation"
    exit 1
  fi
  
  echo "✅ CuraEngine installed successfully"
fi

# Clone or update the ASFO slicer service repo
echo "📥 Downloading ASFO slicer service..."
if [ -d "$INSTALL_DIR/.git" ]; then
  echo "Updating existing installation..."
  cd $INSTALL_DIR
  if ! git fetch origin $BRANCH; then
    echo "⚠️  Git fetch failed, continuing with existing version"
  else
    git reset --hard origin/$BRANCH
  fi
  cd -
else
  rm -rf $INSTALL_DIR
  if ! git clone --depth 1 --branch $BRANCH $REPO_URL $INSTALL_DIR; then
    echo "❌ Failed to clone ASFO repository"
    exit 1
  fi
fi

# Create Python virtual environment
echo "🐍 Setting up Python environment..."
if ! python3 -m venv $VENV_DIR; then
  echo "❌ Failed to create virtual environment"
  exit 1
fi

source $VENV_DIR/bin/activate
if ! pip install --upgrade pip setuptools wheel; then
  echo "❌ Failed to upgrade pip"
  deactivate
  exit 1
fi

if ! pip install -r $INSTALL_DIR/requirements.txt; then
  echo "❌ Failed to install Python dependencies"
  deactivate
  exit 1
fi
deactivate

# Create data directories
echo "📁 Creating data directories..."
mkdir -p $DATA_DIR $GCODE_DIR $STL_DIR

# Initialize database
echo "💾 Initializing database..."
cd $INSTALL_DIR
source $VENV_DIR/bin/activate
python3 -c "from ASFO.database import init_db; init_db()"
deactivate
cd -

# Set permissions
echo "🔒 Setting permissions..."
chown -R $SERVICE_USER:$SERVICE_USER $DATA_DIR $INSTALL_DIR

# Create systemd service file
echo "⚙️  Creating systemd service..."
SERVICE_FILE=/etc/systemd/system/ASFO.service
cat > $SERVICE_FILE <<EOF
[Unit]
Description=ASFO Slicer Service (CuraEngine + FastAPI)
After=network.target

[Service]
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$INSTALL_DIR
Environment="PATH=$VENV_DIR/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin"
Environment="DATA_DIR=$DATA_DIR"
Environment="CURAENGINE_PATH=/usr/local/bin/CuraEngine"
Environment="PYTHONPATH=$INSTALL_DIR"
ExecStart=$VENV_DIR/bin/uvicorn ASFO.app:app --host 0.0.0.0 --port 8080 --workers 1
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable ASFO.service

# Configure Moonraker if installed
MOONRAKER_CONF="/home/pi/printer_data/config/moonraker.conf"
if [ -f "$MOONRAKER_CONF" ]; then
  echo "🔧 Configuring Moonraker..."
  
  # Get local IP address
  LOCAL_IP=$(hostname -I | awk '{print $1}')
  
  # Add CORS domain if not already present
  if ! grep -q "cors_domains:" "$MOONRAKER_CONF"; then
    echo "Adding cors_domains section to moonraker.conf..."
    cat >> "$MOONRAKER_CONF" << EOF

[server]
cors_domains:
    http://${LOCAL_IP}
    http://${LOCAL_IP}:*
EOF
  else
    # Check if our IP is already in cors_domains
    if ! grep -A 10 "cors_domains:" "$MOONRAKER_CONF" | grep -q "$LOCAL_IP"; then
      echo "Adding ${LOCAL_IP} to cors_domains..."
      # Insert after cors_domains: line
      sed -i "/cors_domains:/a\\    http://${LOCAL_IP}\n    http://${LOCAL_IP}:*" "$MOONRAKER_CONF"
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
    
    # Restart Moonraker to apply changes
    if systemctl is-active --quiet moonraker; then
      echo "Restarting Moonraker to apply configuration..."
      systemctl restart moonraker
      sleep 2
    fi
    
    echo "✅ Moonraker configured for ASFO updates"
  else
    echo "✅ Moonraker already configured for ASFO"
  fi
else
  echo "⚠️  Moonraker config not found at $MOONRAKER_CONF"
  echo "   You'll need to manually add the configuration (see below)"
fi

# Start the service
echo "🚀 Starting ASFO slicer service..."
systemctl start ASFO

if systemctl is-active --quiet ASFO.service; then
  echo ""
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "✅ Installation complete!"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo ""
  echo "ASFO Service is running at: http://$(hostname -I | awk '{print $1}'):8080"
  echo ""
  echo "📁 Directories:"
  echo "  • Install:       $INSTALL_DIR"
  echo "  • Data:          $DATA_DIR"
  echo "  • G-codes:       $GCODE_DIR"
  echo "  • STL files:     $STL_DIR"
  echo ""
  echo "🔧 Useful commands:"
  echo "  • Check status:  sudo systemctl status ASFO"
  echo "  • View logs:     sudo journalctl -u ASFO -f"
  echo "  • Restart:       sudo systemctl restart ASFO"
  echo "🔧 Useful commands:"
  echo "  • Check status:  sudo systemctl status ASFO"
  echo "  • View logs:     sudo journalctl -u ASFO -f"
  echo "  • Restart:       sudo systemctl restart ASFO"
  echo "  • Stop:          sudo systemctl stop ASFO"
  echo ""
  echo "🚀 Next steps:"
  echo "  1. Test API:     curl http://localhost:8080/"
  echo "  2. Check version: curl http://localhost:8080/version"
  echo "  3. Go to Mainsail UI → Machine → Update Manager"
  echo "  4. You should see 'ASFO' in the update list"
  echo "  5. Upload an STL and test slicing"
  echo ""
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
else
  echo ""
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "⚠️  Service failed to start!"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo ""
  echo "Check logs for details:"
  echo "  sudo journalctl -u ASFO -n 50 --no-pager"
  echo ""
  echo "Common issues:"
  echo "  • Port 8080 already in use"
  echo "  • Python dependencies failed to install"
  echo "  • Permissions issues"
  echo ""
  echo "To retry installation:"
  echo "  curl -fsSL https://raw.githubusercontent.com/alex006l/ASFO/main/install_ASFO.sh | sudo bash"
  echo ""
  exit 1
fi

exit 0
