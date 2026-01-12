#!/bin/bash
# Git Repository Recovery Script for ASFO on Raspberry Pi
# Run this if you see "Error Recovering ASFO" or checkout errors

set -e

ASFO_DIR="/opt/ASFO"
BACKUP_DIR="/opt/ASFO_backup_$(date +%Y%m%d_%H%M%S)"

echo "=========================================="
echo "ASFO Git Recovery Script"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root: sudo $0"
    exit 1
fi

cd "$ASFO_DIR"

echo "Step 1: Checking Git status..."
git status || true
echo ""

echo "Step 2: Stashing any local changes..."
git stash || true
echo ""

echo "Step 3: Fetching latest from remote..."
git fetch origin || {
    echo "Error: Cannot fetch from remote. Check network connection."
    exit 1
}
echo ""

echo "Step 4: Resetting to origin/main..."
git reset --hard origin/main || {
    echo "Error: Cannot reset to origin/main"
    echo "Attempting more aggressive recovery..."
    
    # Create backup
    echo "Creating backup at $BACKUP_DIR..."
    cp -r "$ASFO_DIR" "$BACKUP_DIR"
    
    # Remove .git and re-clone
    echo "Removing corrupted .git directory..."
    rm -rf .git
    
    echo "Re-initializing repository..."
    git init
    git remote add origin https://github.com/alex006l/ASFO.git
    git fetch origin
    git checkout -b main origin/main
}
echo ""

echo "Step 5: Cleaning untracked files..."
git clean -fd
echo ""

echo "Step 6: Verifying repository state..."
git log --oneline -5
echo ""

echo "Step 7: Checking current branch..."
git branch -v
echo ""

echo "=========================================="
echo "Git recovery complete!"
echo "=========================================="
echo ""
echo "Latest commits:"
git log --oneline -3
echo ""
echo "Current branch: $(git branch --show-current)"
echo ""
echo "Now restart the service:"
echo "  sudo systemctl restart ASFO.service"
echo "  sudo systemctl status ASFO.service"
