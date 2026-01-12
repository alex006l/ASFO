# Quick Start Guide

## Local Development (without Raspberry Pi)

1. **Install dependencies:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Set environment variables:**
   ```bash
   export DATA_DIR="./data"
   export CURAENGINE_PATH="/usr/local/bin/CuraEngine"  # or your path
   ```

3. **Run the service:**
   ```bash
   make run
   # or
   uvicorn ASFO.app:app --host 0.0.0.0 --port 8080 --reload
   ```

4. **Test the API:**
   ```bash
   ./test_api.sh
   # or
   make test
   ```

## Raspberry Pi Installation

### One-Line Install (Recommended)

```bash
curl -fsSL https://raw.githubusercontent.com/alex006l/ASFO/main/install_ASFO.sh | sudo bash
```

Or with wget:
```bash
wget -O - https://raw.githubusercontent.com/alex006l/ASFO/main/install_ASFO.sh | sudo bash
```

### Manual Install

```bash
git clone https://github.com/alex006l/ASFO.git
cd slicer-service
sudo ./install_ASFO.sh
```

This will:
- Build CuraEngine from source
- Create Python venv with dependencies
- Set up systemd service
- Create data directories

After install:
```bash
# Start service
sudo systemctl start ASFO.service

# Check status
sudo systemctl status ASFO.service

# View logs
sudo journalctl -u ASFO.service -f
```

## API Usage Examples

### Upload STL
```bash
curl -F "file=@model.stl" http://localhost:8080/upload-stl
```

### Slice
```bash
curl -X POST http://localhost:8080/slice \
  -H "Content-Type: application/json" \
  -d '{
    "stl_path": "/path/to/uploaded.stl",
    "printer_id": "ender3_01",
    "material": "PLA",
    "profile": "standard",
    "nozzle_size": 0.4
  }'
```

### Generate Calibration Print
```bash
curl -X POST http://localhost:8080/calibration/generate \
  -H "Content-Type: application/json" \
  -d '{
    "printer_id": "ender3_01",
    "calibration_type": "pressure_advance",
    "filament_name": "esun_pla_red",
    "material_type": "PLA",
    "nozzle_temp": 200,
    "bed_temp": 60,
    "start_pa": 0.0,
    "end_pa": 0.1
  }'
```

### Save Filament Calibration
```bash

## Filament Calibration

See [FILAMENT_CALIBRATION.md](FILAMENT_CALIBRATION.md) for the complete calibration workflow.

Quick overview:
1. Generate calibration prints (pressure advance, flow, temperature)
2. Print and inspect results
3. Save calibrated values per filament
4. Use filament-specific profiles for future prints
curl -X POST http://localhost:8080/calibration/save \
  -H "Content-Type: application/json" \
  -d '{
    "printer_id": "ender3_01",
    "filament_name": "esun_pla_red",
    "material_type": "PLA",
    "pressure_advance": 0.055,
    "optimal_nozzle_temp": 205,
    "flow_multiplier": 0.98
  }'
```

### Submit Feedback
```bash
curl -X POST http://localhost:8080/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "printer_id": "ender3_01",
    "material": "PLA",
    "profile": "standard",
    "profile_version": 1,
    "result": "failure",
    "failure_type": "under_extrusion",
    "quality_rating": 2
  }'
```

## Mainsail Integration

See [MAINSAIL_INTEGRATION.md](MAINSAIL_INTEGRATION.md) for detailed UI integration guide.

## Project Structure
```
.
├── README.md                    # Architecture overview
├── QUICKSTART.md               # This file
├── MAINSAIL_INTEGRATION.md     # UI integration guide
├── install_ASFO.sh   # Pi installation script
├── requirements.txt            # Python dependencies
├── requirements-dev.txt        # Dev dependencies
├── Makefile                    # Common commands
├── test_ASFO.py      # Unit tests
├── test_api.sh                 # API integration tests
└── ASFO/
    ├── __init__.py
    ├── app.py                  # FastAPI application
    ├── config.py               # Configuration
    ├── models.py               # Data models
    ├── database.py             # Database setup
    ├── cura_engine.py          # CuraEngine wrapper
    ├── moonraker_client.py     # Moonraker API client
    └── profile_manager.py      # Profile mutations
```

## Next Steps

1. **Test locally** with sample STL files
2. **Deploy to Raspberry Pi** using install script
3. **Integrate with Mainsail** (see MAINSAIL_INTEGRATION.md)
4. **Print and collect feedback** to test mutation logic
5. **Refine mutation rules** based on real-world data

## Troubleshooting

**CuraEngine not found:**
- Check `CURAENGINE_PATH` env var
- Verify installation: `CuraEngine --help`

**Service won't start:**
- Check logs: `sudo journalctl -u ASFO.service`
- Verify permissions on `/var/lib/ASFO/`
- Ensure Python venv is activated

**Slicing fails:**
- Verify CuraEngine can read STL file
- Check profile JSON is valid
- Review CuraEngine output in logs

**Moonraker upload fails:**
- Verify Moonraker URL is correct
- Check network connectivity
- Ensure Moonraker API is accessible
