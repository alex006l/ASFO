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
  
  # Clean up any previous failed attempts
  if [ -d "$CURAENGINE_DIR" ]; then
    echo "Cleaning previous CuraEngine directory..."
    rm -rf $CURAENGINE_DIR
  fi
  
  # Clone with submodules to get all dependencies
  # Note: --depth 1 with --recursive can be problematic, so we clone then init submodules
  echo "Cloning CuraEngine..."
  git clone --depth 1 https://github.com/Ultimaker/CuraEngine.git $CURAENGINE_DIR
  
  echo "Fetching submodule dependencies..."
  cd $CURAENGINE_DIR
  git submodule update --init --recursive --depth 1
  cd -
  
  # Build
  echo "Building CuraEngine..."
  mkdir -p $CURAENGINE_DIR/build
  cd $CURAENGINE_DIR/build
  cmake .. -DCMAKE_BUILD_TYPE=Release
  make -j$(nproc)
  install -m 0755 CuraEngine /usr/local/bin/CuraEngine
  cd -
  echo "✅ CuraEngine installed to /usr/local/bin/CuraEngine"
fi

# Clone or update the ASFO slicer service repo
echo "📥 Downloading ASFO slicer service..."
if [ -d "$INSTALL_DIR/.git" ]; then
  echo "Updating existing installation..."
  cd $INSTALL_DIR
  git fetch origin $BRANCH
  git reset --hard origin/$BRANCH
  cd -
else
  rm -rf $INSTALL_DIR
  git clone --depth 1 --branch $BRANCH $REPO_URL $INSTALL_DIR
fi

# Create Python virtual environment
echo "🐍 Setting up Python environment..."
python3 -m venv $VENV_DIR
source $VENV_DIR/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r $INSTALL_DIR/requirements.txt

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

# Start the service
echo "🚀 Starting ASFO slicer service..."
systemctl start ASFO

[Insta3
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
  echo "  • Stop:          sudo systemctl stop ASFO"
  echo ""
  echo "🚀 Next steps:"
  echo "  1. Test API:     curl http://localhost:8080/"
  echo "  2. Check version: curl http://localhost:8080/version"
  echo "  3. Configure Mainsail (see MAINSAIL_INTEGRATION.md)"
  echo "  4. Upload an STL and test slicing"
  echo ""
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "📦 Enable Updates from Mainsail UI (Optional)"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo ""
  echo "To enable one-click updates from Mainsail's Update Manager,"
  echo "add this to your /home/pi/printer_data/config/moonraker.conf:"
  echo ""
  echo "[update_manager ASFO]"
  echo "type: git_repo"
  echo "path: $INSTALL_DIR"
  echo "origin: $REPO_URL"
  echo "managed_services: ASFO"
  echo "primary_branch: $BRANCH"
  echo "virtualenv: $VENV_DIR"
  echo "requirements: requirements.txt"
  echo "install_script: scripts/install_update.sh"
  echo ""
  echo "Then restart Moonraker:"
  echo "  sudo systemctl restart moonraker"
  echo ""
  echo "📖 See MOONRAKER_UPDATES.md for detailed instructions"
  echo ""
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
