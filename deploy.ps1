#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Deploy ASFO updates to Raspberry Pi
.DESCRIPTION
    This script connects to the Raspberry Pi via SSH, pulls the latest changes
    from the git repository, and restarts the ASFO service.
.PARAMETER PiHost
    The IP address or hostname of the Raspberry Pi (default: 192.168.1.19)
.PARAMETER PiUser
    The username for SSH connection (default: pi)
.PARAMETER PiPassword
    The password for SSH connection (default: raspberry)
.EXAMPLE
    .\deploy.ps1
    Deploy using default settings
.EXAMPLE
    .\deploy.ps1 -PiHost 192.168.1.20 -PiUser admin
    Deploy to a different host with custom username
#>

param(
    [string]$PiHost = "192.168.1.19",
    [string]$PiUser = "pi",
    [string]$PiPassword = "raspberry"
)

$ErrorActionPreference = "Stop"

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "   ASFO Deployment Script" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# Check if plink (PuTTY) is available, otherwise use ssh
$usePlink = Get-Command plink -ErrorAction SilentlyContinue

if ($usePlink) {
    Write-Host "[INFO] Using PuTTY's plink for SSH connection" -ForegroundColor Yellow
    $sshCmd = "plink"
} else {
    Write-Host "[INFO] Using OpenSSH for connection" -ForegroundColor Yellow
    $sshCmd = "ssh"
}

Write-Host "[1/5] Testing connection to Pi at $PiHost..." -ForegroundColor Green

# Test connection
try {
    if ($usePlink) {
        # For plink, we need to accept the host key first
        echo "y" | & plink -batch -pw $PiPassword "${PiUser}@${PiHost}" "echo 'Connection successful'" 2>$null
    } else {
        # For OpenSSH
        & ssh -o "StrictHostKeyChecking=no" -o "PasswordAuthentication=yes" "${PiUser}@${PiHost}" "echo 'Connection successful'" 2>$null
    }
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ Connection successful!" -ForegroundColor Green
    } else {
        throw "Connection test failed"
    }
} catch {
    Write-Host "  ✗ Failed to connect to Pi" -ForegroundColor Red
    Write-Host "  Make sure the Pi is powered on and accessible at $PiHost" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "[2/5] Checking ASFO installation on Pi..." -ForegroundColor Green

# Commands to execute on the Pi
$deployCommands = @"
# Check if ASFO directory exists
if [ ! -d "/home/pi/ASFO" ]; then
    echo "ERROR: ASFO directory not found at /home/pi/ASFO"
    exit 1
fi

echo "✓ ASFO directory found"

# Navigate to ASFO directory
cd /home/pi/ASFO

# Show current version
echo ""
echo "Current version:"
git describe --tags --always 2>/dev/null || echo "Unable to determine version"

echo ""
echo "Pulling latest changes..."

# Pull latest changes
git fetch origin
git pull origin main

if [ \$? -eq 0 ]; then
    echo "✓ Git pull successful"
else
    echo "✗ Git pull failed"
    exit 1
fi

# Show new version
echo ""
echo "New version:"
git describe --tags --always

# Check if systemd service exists
if systemctl list-units --full -all | grep -Fq 'asfo.service'; then
    echo ""
    echo "Restarting ASFO service..."
    sudo systemctl restart asfo.service
    
    if [ \$? -eq 0 ]; then
        echo "✓ Service restarted successfully"
        
        # Wait a moment for service to start
        sleep 2
        
        # Check service status
        if systemctl is-active --quiet asfo.service; then
            echo "✓ Service is running"
        else
            echo "⚠ Service may not be running properly"
            sudo systemctl status asfo.service --no-pager -l
        fi
    else
        echo "✗ Failed to restart service"
        exit 1
    fi
else
    echo ""
    echo "⚠ ASFO systemd service not found"
    echo "You may need to restart ASFO manually"
fi

echo ""
echo "Deployment complete!"
"@

Write-Host ""
Write-Host "[3/5] Executing deployment commands on Pi..." -ForegroundColor Green
Write-Host ""

# Execute commands on Pi
try {
    if ($usePlink) {
        echo $PiPassword | & plink -batch -pw $PiPassword "${PiUser}@${PiHost}" $deployCommands
    } else {
        # For OpenSSH, we'll use expect or sshpass if available, otherwise prompt for password
        $deployCommands | & ssh -o "StrictHostKeyChecking=no" "${PiUser}@${PiHost}"
    }
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "[4/5] Deployment commands completed successfully" -ForegroundColor Green
    } else {
        throw "Deployment commands failed with exit code $LASTEXITCODE"
    }
} catch {
    Write-Host ""
    Write-Host "[4/5] Deployment failed!" -ForegroundColor Red
    Write-Host "  Error: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "[5/5] Verifying deployment..." -ForegroundColor Green

# Verify the service is running
try {
    if ($usePlink) {
        $statusOutput = echo $PiPassword | & plink -batch -pw $PiPassword "${PiUser}@${PiHost}" "curl -s http://localhost:5000/version 2>/dev/null || echo 'Service check failed'"
    } else {
        $statusOutput = & ssh -o "StrictHostKeyChecking=no" "${PiUser}@${PiHost}" "curl -s http://localhost:5000/version 2>/dev/null || echo 'Service check failed'"
    }
    
    if ($statusOutput -match "version") {
        Write-Host "  ✓ ASFO service is responding" -ForegroundColor Green
        Write-Host "  Response: $statusOutput" -ForegroundColor Gray
    } else {
        Write-Host "  ⚠ Unable to verify service status" -ForegroundColor Yellow
        Write-Host "  The service may still be starting up" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  ⚠ Could not verify service status" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "   Deployment Complete!" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "ASFO Web UI: http://${PiHost}:5000/ui/index.html" -ForegroundColor Green
Write-Host "API Docs: http://${PiHost}:5000/docs" -ForegroundColor Green
Write-Host ""
