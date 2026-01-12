"""Configuration for slicer service."""
import os
from pathlib import Path

# Directories
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = Path(os.getenv("DATA_DIR", "/var/lib/ASFO"))
GCODE_DIR = DATA_DIR / "gcodes"
PROFILES_DIR = DATA_DIR / "profiles"
STL_TEMP_DIR = DATA_DIR / "stl_temp"
DATABASE_PATH = DATA_DIR / "ASFO.db"

# CuraEngine (Debian package installs to /usr/bin)
CURAENGINE_PATH = os.getenv("CURAENGINE_PATH", "/usr/bin/CuraEngine")

# API settings
API_KEY = os.getenv("API_KEY", "dev_key_change_in_production")

# Moonraker default (can be overridden per request)
DEFAULT_MOONRAKER_URL = os.getenv("MOONRAKER_URL", "http://localhost:7125")

# Create directories if they don't exist
for directory in [DATA_DIR, GCODE_DIR, PROFILES_DIR, STL_TEMP_DIR]:
    directory.mkdir(parents=True, exist_ok=True)
