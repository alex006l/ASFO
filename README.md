# Slicer Service

**CuraEngine-based slicing service with feedback-driven profile optimization for 3D printers.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com)

## What is this?

A standalone slicing service that:
- Accepts STL files and slices them using CuraEngine
- Uploads G-code to Moonraker (Klipper/Mainsail)
- Collects feedback after prints
- Automatically tunes slicing profiles based on real results
- Supports multi-printer setups from day one

## Why?

- **Mainsail has no slicer** — it's a pure frontend talking to Moonraker
- **Manual profile tuning is tedious** — let the system learn from print outcomes
- **Clean architecture** — service runs independently, integrates cleanly
- **No black-box ML** — simple, bounded, reversible rule-based mutations

## Architecture

```
┌─────────────┐
│  Mainsail   │  ← UI only (Vue.js SPA)
└─────┬───────┘
      │ REST / WebSocket
┌─────▼───────┐
│ Moonraker   │  ← Printer control + files
└─────┬───────┘
      │ REST
┌─────▼─────────────────────────────┐
│ Slicer Service (FastAPI + Python) │
│ - CuraEngine CLI wrapper           │
│ - Profile versioning               │
│ - Feedback loop                    │
│ - Rule-based optimization          │
└────────────────────────────────────┘
```

## Quick Start

**Raspberry Pi (one-line install):**
```bash
curl -fsSL https://raw.githubusercontent.com/alex006l/ASFO/main/install_ASFO.sh | sudo bash
```

**Local development:**
```bash
git clone https://github.com/alex006l/ASFO.git
cd slicer-service
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
make run
```

See [QUICKSTART.md](QUICKSTART.md) for full instructions.

## Features

✅ **CuraEngine integration** — proven, fast ARM-compatible slicer  
✅ **Klipper-optimized** — automatic layer tracking, timelapse support, and metadata  
✅ **Transparent thumbnails** — orange/coral 3D previews for Mainsail/Fluidd  
✅ **Multi-printer support** — per-printer profiles and feedback  
✅ **Filament-specific calibration** — pressure advance, flow, temperature per spool  
✅ **Auto-generated calibration prints** — from printer.cfg analysis  
✅ **Profile versioning** — every change is tracked and reversible  
✅ **Feedback-driven optimization** — real-world results improve profiles  
✅ **Rule-based mutations** — small, bounded, deterministic changes  
✅ **Moonraker upload** — seamless integration with existing workflow  
✅ **Moonraker update manager** — update from Mainsail UI  
✅ **RESTful API** — easy integration with any UI  
✅ **SQLite storage** — lightweight, no external database needed  

## API Endpoints

**Slicing:**
- `POST /upload-stl` — Upload STL file
- `POST /slice` — Slice STL with specified profile
- `POST /upload-to-moonraker` — Upload G-code and optionally start print

**Feedback & Learning:**
- `POST /feedback` — Submit print feedback
- `GET /profiles/{printer_id}/{material}` — Get profile history
- `GET /feedback/{printer_id}` — Get feedback history

**Calibration (NEW):**
- `POST /calibration/generate` — Generate calibration test prints
- `POST /calibration/save` — Save filament calibration results
- `GET /filaments/{printer_id}` — List all calibrated filaments
- `GET /filaments/{printer_id}/{filament_name}` — Get specific filament profile

## Feedback Loop

After each print, users answer:
- ✅ Success or ❌ Failure?
- If failure: what type? (under-extrusion, stringing, adhesion, etc.)
- Optional: quality rating (1-5)
- Optional: notes

The system applies small, reversible mutations:
- Under-extrusion → +2% flow
- Stringing → +0.2mm retraction, -5°C
- Adhesion → +5°C bed, -10% first layer speed

## Documentation

| File | Purpose |
|------|---------|
| [README.md](README.md) | This file - main overview |
| [QUICKSTART.md](QUICKSTART.md) | Installation & usage guide |
| [DEPLOYMENT.md](DEPLOYMENT.md) | GitHub publishing & deployment |
| [KLIPPER_INTEGRATION.md](KLIPPER_INTEGRATION.md) | Klipper features & configuration |
| [MAINSAIL_INTEGRATION.md](MAINSAIL_INTEGRATION.md) | UI integration guide |
| [FILAMENT_CALIBRATION.md](FILAMENT_CALIBRATION.md) | Calibration workflow & guide |
| [READY_TO_DEPLOY.md](READY_TO_DEPLOY.md) | Pre-publish checklist |

## Mainsail Integration

Three approaches:
1. **Iframe panel** (quickest, no Mainsail changes)
2. **Vue plugin** (native feel, requires Mainsail fork/PR)
3. **Native extension** (future, if Mainsail adds plugin API)

See [MAINSAIL_INTEGRATION.md](MAINSAIL_INTEGRATION.md) for details.
calibration.py          # Calibration print generator (NEW)
├── printer_config.py       # Klipper printer.cfg parser (NEW)
├── 
## Project Structure

```
ASFO/
├── app.py                  # FastAPI endpoints
├── cura_engine.py          # CuraEngine wrapper
├── moonraker_client.py     # Moonraker API client
├── profile_manager.py      # Profile mutations
├── models.py               # Data models
├── database.py             # SQLite setup
└── config.py               # Configuration
```

## Tech Stack

- **Backend:** Python 3.10+ with FastAPI
- **Slicer:** CuraEngine (CLI)
- **Database:** SQLite (via SQLModel)
- **Deployment:** systemd service on Raspberry Pi
- **Testing:** pytest

## Testing

```bash
# Unit tests
make test

# API integration tests
./test_api.sh
```

## Deployment

**Raspberry Pi (recommended):**
```bash
sudo ./install_ASFO.sh
```

This builds CuraEngine, sets up Python venv, and creates a systemd service.

**Docker (alternative):**
```bash
# TODO: Add Dockerfile
```

## Configuration

Environment variables:
- `DATA_DIR` — Data storage path (default: `/var/lib/ASFO`)
- `CURAENGINE_PATH` — CuraEngine binary path (default: `/usr/local/bin/CuraEngine`)
- `MOONRAKER_URL` — Default Moonraker URL (default: `http://localhost:7125`)
- `API_KEY` — API key for protected endpoints (default: `dev_key_change_in_production`)

## Roadmap

- [x] Core slicing service
- [x] Feedback endpoints
- [x] Profile mutations
- [x] Moonraker upload
- [x] Filament-specific calibration
- [x] Pressure advance testing
- [x] Printer.cfg parsing
- [x] Klipper integration (layer tracking, timelapse)
- [x] Transparent thumbnails for Mainsail
- [ ] Mainsail iframe UI
- [ ] WebSocket for real-time progress
- [ ] Advanced analytics dashboard
- [ ] Object cancellation support
- [ ] Cloud profile sync
- [ ] Print farm management
- [ ] Auto-analysis of calibration prints (camera)

## Publishing to GitHub

To publish this project and enable one-line install:

```bash
./publish_to_github.sh
```

Or manually follow the steps in [DEPLOYMENT.md](DEPLOYMENT.md).

## Contributing

PRs welcome! Focus areas:
- Additional mutation rules
- Material-specific defaults
- CuraEngine profile improvements
- Mainsail UI integration
- Documentation

## License

MIT License - see [LICENSE](LICENSE) file for details

## Credits

Built with:
- FastAPI
- CuraEngine (Ultimaker)
- SQLModel
- Moonraker API

Inspired by industrial control systems that use human feedback loops.
