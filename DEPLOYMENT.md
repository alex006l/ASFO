# Deployment Guide

## Publishing to GitHub

### 1. Create GitHub Repository

```bash
# Initialize git (if not already done)
cd /Users/alejandroleal/Desktop/3D
git init

# Add all files
git add .

# Create initial commit
git commit -m "Initial commit: Slicer service with CuraEngine and feedback loop"

# Create GitHub repo (replace YOUR_USERNAME)
# Option A: Using GitHub CLI
gh repo create slicer-service --public --source=. --remote=origin --push

# Option B: Manual
# - Go to https://github.com/new
# - Create repo named "slicer-service"
# - Then run:
git remote add origin https://github.com/YOUR_USERNAME/slicer-service.git
git branch -M main
git push -u origin main
```

### 2. Update Install Script URL

After creating the repo, update these files with your actual GitHub username:

**Files to update:**
- `install_slicer_service.sh` (line 5)
- `README_MAIN.md` (Quick Start section)
- `QUICKSTART.md` (Installation section)

Replace `YOUR_USERNAME` with your actual GitHub username.

### 3. Test One-Line Install

From any Raspberry Pi:

```bash
curl -fsSL https://raw.githubusercontent.com/YOUR_USERNAME/slicer-service/main/install_slicer_service.sh | sudo bash
```

## What the Install Script Does

1. ✅ Updates system packages
2. ✅ Installs build dependencies (cmake, boost, eigen3, etc.)
3. ✅ Builds CuraEngine from source (~10-20 min on Pi 4)
4. ✅ Clones slicer service repo
5. ✅ Creates Python virtual environment
6. ✅ Installs Python dependencies
7. ✅ Creates systemd service
8. ✅ Starts service automatically
9. ✅ Enables service on boot

## Post-Install

The service will be available at:
```
http://<pi-ip-address>:8080
```

Test it:
```bash
curl http://localhost:8080/
```

## Configuration

After install, you can configure via environment variables in:
```
/etc/systemd/system/slicer_service.service
```

Available env vars:
- `DATA_DIR` — Data storage path
- `CURAENGINE_PATH` — CuraEngine binary location
- `MOONRAKER_URL` — Default Moonraker URL
- `API_KEY` — API authentication key

After changing config:
```bash
sudo systemctl daemon-reload
sudo systemctl restart slicer_service
```

## Updating

To update an existing installation:

```bash
# Pull latest changes
cd /opt/slicer_service
sudo git pull

# Restart service
sudo systemctl restart slicer_service
```

Or re-run the install script:
```bash
curl -fsSL https://raw.githubusercontent.com/YOUR_USERNAME/slicer-service/main/install_slicer_service.sh | sudo bash
```

## Uninstall

```bash
# Stop and disable service
sudo systemctl stop slicer_service
sudo systemctl disable slicer_service

# Remove service file
sudo rm /etc/systemd/system/slicer_service.service
sudo systemctl daemon-reload

# Remove installation
sudo rm -rf /opt/slicer_service
sudo rm -rf /var/lib/slicer_service

# Optionally remove CuraEngine
sudo rm /usr/local/bin/CuraEngine
sudo rm -rf /opt/CuraEngine

# Remove service user
sudo userdel slicer
```

## Troubleshooting

### Service won't start

```bash
# Check detailed logs
sudo journalctl -u slicer_service -n 100 --no-pager

# Check service status
sudo systemctl status slicer_service
```

### CuraEngine build fails

- Ensure sufficient disk space (>2GB free)
- Check build dependencies are installed
- Try building manually:
  ```bash
  cd /opt/CuraEngine
  mkdir -p build && cd build
  cmake .. -DCMAKE_BUILD_TYPE=Release
  make -j$(nproc)
  ```

### Port 8080 already in use

Change port in service file:
```bash
sudo nano /etc/systemd/system/slicer_service.service
# Change --port 8080 to --port 8081 (or other)
sudo systemctl daemon-reload
sudo systemctl restart slicer_service
```

### Permission errors

Ensure service user has correct permissions:
```bash
sudo chown -R slicer:slicer /var/lib/slicer_service
sudo chown -R slicer:slicer /opt/slicer_service
```

## Security Recommendations

1. **Change default API key:**
   ```bash
   sudo systemctl edit slicer_service
   # Add: Environment="API_KEY=your_secure_key_here"
   ```

2. **Firewall (optional):**
   ```bash
   sudo ufw allow 8080/tcp
   sudo ufw enable
   ```

3. **Reverse proxy (production):**
   Use nginx or Caddy to add HTTPS and authentication

4. **Network isolation:**
   Keep service on local network, don't expose to internet

## Performance Tips

**For Raspberry Pi 3 or older:**
- Reduce uvicorn workers to 1 (already default)
- Consider using faster SD card
- Slicing will be slower (~2-5x)

**For Raspberry Pi 4/5:**
- Can increase workers to 2-4
- Use SSD instead of SD card for better performance
- Slicing should be reasonably fast

**For print farms:**
- Run service on dedicated Pi (not on printer Pi)
- Use Pi 4 8GB for handling multiple printers
- Consider load balancing if >10 printers

## GitHub Actions (Optional)

Add `.github/workflows/test.yml` for automated testing:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - run: pip install -r requirements.txt -r requirements-dev.txt
      - run: pytest test_slicer_service.py -v
```

## Docker Alternative (Future)

For those who prefer Docker over native install, a Dockerfile could be added:

```dockerfile
FROM python:3.10-slim

# Install dependencies and build CuraEngine
RUN apt-get update && apt-get install -y ...
# ... (CuraEngine build steps)

# Copy service
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt

CMD ["uvicorn", "slicer_service.app:app", "--host", "0.0.0.0", "--port", "8080"]
```

This is not currently implemented but could be added if there's demand.
