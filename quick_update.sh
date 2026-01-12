#!/bin/bash
# Quick ASFO Update - Run this directly on the Raspberry Pi
# Usage: sudo bash quick_update.sh

set -e

echo "==================================="
echo "ASFO Quick Update"
echo "==================================="

cd /opt/ASFO

echo "1. Checking current state..."
git status

echo ""
echo "2. Stashing local changes..."
git stash

echo ""
echo "3. Fetching from GitHub..."
git fetch origin --prune

echo ""
echo "4. Resetting to latest main..."
git reset --hard origin/main

echo ""
echo "5. Cleaning untracked files..."
git clean -fd

echo ""
echo "6. Restarting ASFO service..."
systemctl restart ASFO.service

echo ""
echo "7. Checking service status..."
systemctl status ASFO.service --no-pager

echo ""
echo "==================================="
echo "Update complete!"
echo "Latest commit:"
git log -1 --oneline
echo ""
echo "Open http://$(hostname -I | awk '{print $1}'):8080 to see the new UI"
echo "==================================="
