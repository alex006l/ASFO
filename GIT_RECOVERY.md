# Git Recovery Guide for ASFO

If you see "Error Recovering ASFO" or "Error running shell command: 'git -C /opt/ASFO checkout -q main'", follow these steps:

## Quick Fix (Most Common)

SSH into your Pi and run:

```bash
cd /opt/ASFO
sudo git fetch origin
sudo git reset --hard origin/main
sudo git clean -fd
sudo systemctl restart ASFO.service
```

## Automatic Recovery Script

Or use the automated recovery script:

```bash
sudo bash /opt/ASFO/scripts/recover_git.sh
```

This script will:
1. Check Git status
2. Stash local changes
3. Fetch latest from GitHub
4. Reset to origin/main
5. Clean untracked files
6. Verify repository state

## Manual Recovery (If Above Fails)

If the repository is severely corrupted:

```bash
# Backup current directory
sudo cp -r /opt/ASFO /opt/ASFO_backup_manual

# Remove and re-clone
sudo rm -rf /opt/ASFO
sudo git clone https://github.com/alex006l/ASFO.git /opt/ASFO
cd /opt/ASFO

# Ensure proper ownership
sudo chown -R pi:pi /opt/ASFO

# Activate venv and install dependencies
source venv/bin/activate
pip install -r requirements.txt

# Restart service
sudo systemctl restart ASFO.service
sudo systemctl status ASFO.service
```

## Common Causes

1. **Moonraker trying to update while you're manually pulling** - Conflict between manual git operations and Moonraker's update manager
2. **Uncommitted local changes** - Files modified locally that conflict with remote
3. **Corrupted .git directory** - Rare but can happen after power loss

## Prevention

To avoid future issues:

### Option 1: Let Moonraker Handle Updates
Don't manually run `git pull`. Instead, use Mainsail's update manager.

### Option 2: Disable Moonraker Updates
If you prefer manual control, remove or disable the update manager in `moonraker.conf`:

```cfg
# Comment out or remove:
# [update_manager ASFO]
# type: git_repo
# path: /opt/ASFO
# ...
```

Then manually update when needed:
```bash
cd /opt/ASFO
sudo git fetch origin
sudo git reset --hard origin/main
sudo systemctl restart ASFO.service
```

## After Recovery

1. **Verify service is running**:
   ```bash
   sudo systemctl status ASFO.service
   ```

2. **Check logs for errors**:
   ```bash
   sudo journalctl -u ASFO.service -n 50 --no-pager
   ```

3. **Test API**:
   ```bash
   curl http://localhost:8080/
   ```

4. **Check latest commit**:
   ```bash
   cd /opt/ASFO && git log --oneline -5
   ```

Expected latest commits:
- `62a59d9` - Complete Klipper integration: CLI preprocessor, optimized settings, documentation
- `f4bd915` - Add transparent background thumbnails and Klipper preprocessor

## Still Having Issues?

If recovery fails, check:
1. **Network connectivity**: `ping github.com`
2. **Disk space**: `df -h`
3. **Git version**: `git --version` (needs 2.x+)
4. **Permissions**: `ls -la /opt/ASFO`

The service should still work even if Git is in a weird state, as long as the Python files are intact.
