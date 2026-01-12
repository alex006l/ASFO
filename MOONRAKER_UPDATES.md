# Moonraker Update Manager Setup

## Overview

The Slicer Service integrates with Moonraker's update manager, allowing you to update it directly from Mainsail's UI, just like Klipper, Moonraker, and Mainsail itself.

## Benefits

✅ **One-click updates** from Mainsail UI  
✅ **Automatic dependency management** — Python packages updated automatically  
✅ **Service restart** — automatic restart after update  
✅ **Rollback support** — revert to previous version if needed  
✅ **Update notifications** — see when updates are available  

## Setup Instructions

### 1. Add Configuration to Moonraker

Edit your `moonraker.conf` file (usually at `/home/pi/printer_data/config/moonraker.conf`):

```bash
sudo nano /home/pi/printer_data/config/moonraker.conf
```

Add this section at the end:

```ini
[update_manager ASFO]
type: git_repo
path: /opt/ASFO
origin: https://github.com/alex006l/ASFO.git
managed_services: ASFO
primary_branch: main
virtualenv: /opt/ASFO/venv
requirements: requirements.txt
install_script: scripts/install_update.sh
```

### 2. Restart Moonraker

```bash
sudo systemctl restart moonraker
```

### 3. Verify in Mainsail

1. Open Mainsail in your browser
2. Navigate to **Machine** > **Update Manager**
3. You should see "ASFO" listed alongside other components

## Using the Update Manager

### Check for Updates

The update manager automatically checks for updates periodically. When updates are available:

1. A notification appears in Mainsail
2. The "ASFO" entry shows "Update available"
3. Click the **Update** button

### Update Process

When you click Update:

1. Moonraker fetches latest code from GitHub
2. Runs the update script (`scripts/install_update.sh`)
3. Updates Python dependencies
4. Restarts the ASFO
5. Shows success or error message

**During update:** The service will be briefly unavailable (10-30 seconds).

### Rollback

If an update causes issues:

1. Go to Machine > Update Manager
2. Find "ASFO"
3. Click the dropdown arrow next to Update
4. Select **"Rollback to previous version"**
5. Confirm rollback

The service will revert to the previous commit.

### Manual Update Check

You can also check for updates via API:

```bash
curl http://localhost:8080/check-updates
```

Response:
```json
{
  "update_available": true,
  "commits_behind": 3,
  "message": "3 update(s) available"
}
```

## Version Information

Get current version:

```bash
curl http://localhost:8080/version
```

Response:
```json
{
  "version": "0.1.0",
  "commit": "a1b2c3d4",
  "branch": "main",
  "is_dirty": false
}
```

## Troubleshooting

### Update Manager Not Showing

**Check Moonraker logs:**
```bash
sudo journalctl -u moonraker -n 50
```

**Common issues:**
- Config syntax error (check for typos)
- Path doesn't exist (`/opt/ASFO`)
- Git repository not initialized
- Moonraker needs restart

### Update Fails

**Check what went wrong:**
```bash
sudo journalctl -u ASFO -n 100
```

**Common fixes:**
- Disk space full (need >500MB free)
- Network connection issues
- Git repository corrupted (re-clone)
- Python dependency conflicts (check logs)

**Recovery:**
If update breaks the service, rollback or manually reset:

```bash
cd /opt/ASFO
sudo git reset --hard origin/main
sudo systemctl restart ASFO
```

### Update Script Permissions

If update fails with permission error:

```bash
sudo chmod +x /opt/ASFO/scripts/install_update.sh
sudo chown -R slicer:slicer /opt/ASFO
```

## Advanced Configuration

### Custom Branch

To track a different branch (e.g., `develop`):

```ini
[update_manager ASFO]
type: git_repo
path: /opt/ASFO
origin: https://github.com/alex006l/ASFO.git
managed_services: ASFO
primary_branch: develop  # Changed from main
virtualenv: /opt/ASFO/venv
requirements: requirements.txt
install_script: scripts/install_update.sh
```

### Update Notifications

Configure notification settings in `moonraker.conf`:

```ini
[update_manager]
enable_auto_refresh: True
refresh_interval: 24  # Check for updates every 24 hours
```

### Multiple Instances

For multiple printers, use unique names:

```ini
[update_manager ASFO_printer1]
type: git_repo
path: /opt/ASFO
# ... rest of config

[update_manager ASFO_printer2]
type: git_repo
path: /opt/ASFO_2
# ... rest of config
```

## Security Notes

- Updates are pulled from the configured GitHub repository
- Only install updates from trusted sources
- Review changelog before updating production systems
- Test updates on a dev printer first if possible
- Rollback is always available

## Automatic Updates

To enable automatic updates (not recommended for production):

```ini
[update_manager ASFO]
type: git_repo
path: /opt/ASFO
origin: https://github.com/alex006l/ASFO.git
managed_services: ASFO
primary_branch: main
virtualenv: /opt/ASFO/venv
requirements: requirements.txt
install_script: scripts/install_update.sh
enable_auto_refresh: True
# Automatic updates disabled by default - uncomment to enable:
# is_system_service: False
```

**Recommendation:** Keep automatic updates disabled and update manually after reviewing changes.

## Integration with CI/CD

The update system works seamlessly with GitHub releases:

1. Create a release tag on GitHub
2. Moonraker detects the new version
3. Users see update notification in Mainsail
4. One-click update to the new release

## FAQ

**Q: Will updates affect my calibrated profiles?**  
A: No, all data in `/var/lib/ASFO/` is preserved during updates.

**Q: Can I disable updates?**  
A: Yes, remove the `[update_manager ASFO]` section from moonraker.conf.

**Q: How do I see what changed in an update?**  
A: Check the GitHub repository commit history or release notes.

**Q: What if I want to stay on a specific version?**  
A: Use git to checkout a specific tag/commit, then disable the update manager entry.

**Q: Does this update CuraEngine?**  
A: No, CuraEngine is installed separately. To update CuraEngine, rebuild it manually.

## Related Documentation

- [Moonraker Update Manager Docs](https://moonraker.readthedocs.io/en/latest/configuration/#update_manager)
- [DEPLOYMENT.md](DEPLOYMENT.md) — Manual update methods
- [MAINSAIL_INTEGRATION.md](MAINSAIL_INTEGRATION.md) — Full integration guide
