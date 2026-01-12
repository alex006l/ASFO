# Moonraker Update Manager Integration ✅

The slicer service now integrates with Moonraker's update manager, allowing users to update it directly from Mainsail's UI!

## What Was Added

### 1. Core Files
- **moonraker_update.conf** — Config snippet for users to add to their moonraker.conf
- **scripts/install_update.sh** — Update script called by Moonraker during updates
- **slicer_service/version.py** — Version info and update check functionality

### 2. New API Endpoints
- `GET /version` — Returns current version, commit hash, and branch info
- `GET /check-updates` — Checks if updates are available from GitHub

### 3. Documentation
- **MOONRAKER_UPDATES.md** — Complete guide to setup and usage
- **MAINSAIL_INTEGRATION.md** — Updated with update manager section
- **DEPLOYMENT.md** — Added update methods (UI, manual, re-install)
- **README.md** — Added update manager to feature list

### 4. Install Script Enhancement
- **install_slicer_service.sh** — Now shows Moonraker config snippet after install

## How It Works

1. **User adds config** to `moonraker.conf`:
```ini
[update_manager slicer_service]
type: git_repo
path: /opt/slicer_service
origin: https://github.com/alex006l/ASFO.git
managed_services: slicer_service
primary_branch: main
virtualenv: /opt/slicer_service/venv
requirements: requirements.txt
install_script: scripts/install_update.sh
```

2. **Moonraker detects** when new commits are pushed to GitHub

3. **User clicks "Update"** in Mainsail UI

4. **Moonraker executes:**
   - `git pull` to fetch latest code
   - Runs `scripts/install_update.sh` to update dependencies
   - Restarts `slicer_service` systemd service

5. **Update complete** — service running latest version

## User Benefits

✅ **One-click updates** from Mainsail UI  
✅ **No SSH required** — update from browser  
✅ **Automatic dependency updates** — Python packages updated automatically  
✅ **Service restart** — automatic restart after update  
✅ **Rollback support** — revert to previous version if needed  
✅ **Update notifications** — see when updates are available  
✅ **Same UX as Klipper/Moonraker** — familiar update flow  

## Testing

To test locally:

```bash
# Start the service
make run

# In another terminal, check version
curl http://localhost:8080/version

# Check for updates (requires git fetch)
curl http://localhost:8080/check-updates
```

Expected response for `/version`:
```json
{
  "version": "0.1.0",
  "commit": "a1b2c3d4",
  "branch": "main",
  "is_dirty": false
}
```

## For Users

After installation, users can enable updates by:

1. Editing their moonraker.conf
2. Adding the `[update_manager slicer_service]` section
3. Restarting Moonraker

Then updates appear in **Mainsail > Machine > Update Manager** alongside Klipper, Moonraker, and Mainsail.

## Files Changed

- ✅ moonraker_update.conf (new)
- ✅ scripts/install_update.sh (new)
- ✅ slicer_service/version.py (new)
- ✅ slicer_service/app.py (updated with version endpoints)
- ✅ MOONRAKER_UPDATES.md (new)
- ✅ MAINSAIL_INTEGRATION.md (updated)
- ✅ DEPLOYMENT.md (updated)
- ✅ README.md (updated)
- ✅ READY_TO_DEPLOY.md (updated)
- ✅ install_slicer_service.sh (updated)

## Next Steps

1. Commit and push these changes
2. Users will see the update in Mainsail after adding the config
3. Future updates are one-click from Mainsail UI

## Comparison

**Before:** Users had to SSH in and run `git pull` + restart manually  
**After:** Click "Update" button in Mainsail UI ✨
