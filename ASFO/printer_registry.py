"""Printer registry and discovery."""
import os
import json
import re
from pathlib import Path
from typing import Dict, List, Optional
from pydantic import BaseModel
from .config import DATA_DIR

class PrinterNode(BaseModel):
    id: str
    name: str
    config_path: str
    moonraker_url: str
    is_default: bool = False

class PrinterRegistry:
    def __init__(self, config_file: Path = DATA_DIR / "printers.json"):
        self.config_file = config_file
        self._printers: Dict[str, PrinterNode] = {}
        self.load()
        if not self._printers:
            self.discover()

    def load(self):
        """Load printers from JSON."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    for p in data:
                        self._printers[p['id']] = PrinterNode(**p)
            except Exception as e:
                print(f"Failed to load printer registry: {e}")

    def save(self):
        """Save printers to JSON."""
        data = [p.dict() for p in self._printers.values()]
        with open(self.config_file, 'w') as f:
            json.dump(data, f, indent=2)

    def discover(self):
        """Auto-discover Klipper instances on the system."""
        home = Path("/home/pi")
        if not home.exists():
            # Dev environment fallback
            self.add_printer(PrinterNode(
                id="default", name="Default Printer", 
                config_path="/tmp/printer.cfg", 
                moonraker_url="http://localhost:7125",
                is_default=True
            ))
            return

        # Check default printer_data
        if (home / "printer_data").exists():
            self.add_printer(PrinterNode(
                id="printer_1", name="Main Printer",
                config_path=str(home / "printer_data/config/printer.cfg"),
                moonraker_url="http://localhost:7125",
                is_default=True
            ))

        # Check additional instances printer_N_data
        for path in home.glob("printer_*_data"):
            match = re.search(r"printer_(\d+)_data", path.name)
            if match:
                idx = int(match.group(1))
                # Port typically 7125 + (idx - 1) for idx=1? No, usually instance 2 is 7126.
                # Assuming index maps to port offset.
                port = 7125 + (idx - 1)
                self.add_printer(PrinterNode(
                    id=f"printer_{idx}", name=f"Printer {idx}",
                    config_path=str(path / "config/printer.cfg"),
                    moonraker_url=f"http://localhost:{port}",
                    is_default=False
                ))

    def add_printer(self, printer: PrinterNode):
        self._printers[printer.id] = printer
        self.save()

    def get_printer(self, printer_id: str) -> Optional[PrinterNode]:
        return self._printers.get(printer_id)

    def get_all(self) -> List[PrinterNode]:
        return list(self._printers.values())

    def get_default(self) -> Optional[PrinterNode]:
        for p in self._printers.values():
            if p.is_default:
                return p
        return list(self._printers.values())[0] if self._printers else None
