#!/usr/bin/env bash
# Update script for Moonraker update manager
# This script is called when updating via Mainsail UI

set -e

INSTALL_DIR="${INSTALL_DIR:-/opt/ASFO}"
VENV_DIR="$INSTALL_DIR/venv"

echo "Updating Slicer Service dependencies..."

# Activate virtual environment
source "$VENV_DIR/bin/activate"

# Update Python dependencies
pip install --upgrade pip
pip install -r "$INSTALL_DIR/requirements.txt" --upgrade

echo "Slicer Service dependencies updated successfully"
