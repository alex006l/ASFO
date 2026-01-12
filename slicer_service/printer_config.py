"""Klipper printer.cfg parser and printer capabilities extractor."""
import re
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class PrinterCapabilities:
    """Extracted printer capabilities from printer.cfg."""
    # Kinematic limits
    max_velocity: float = 300.0
    max_accel: float = 3000.0
    max_z_velocity: float = 15.0
    max_z_accel: float = 300.0
    
    # Build volume
    x_min: float = 0.0
    x_max: float = 220.0
    y_min: float = 0.0
    y_max: float = 220.0
    z_min: float = 0.0
    z_max: float = 250.0
    
    # Extruder
    max_extrude_only_velocity: float = 120.0
    max_extrude_only_accel: float = 1500.0
    nozzle_diameter: float = 0.4
    filament_diameter: float = 1.75
    max_temp: float = 300.0
    min_temp: float = 0.0
    
    # Pressure advance (if configured)
    pressure_advance: Optional[float] = None
    pressure_advance_smooth_time: Optional[float] = None
    
    # Bed
    bed_max_temp: float = 120.0
    
    # Features
    has_bltouch: bool = False
    has_input_shaper: bool = False
    has_pressure_advance: bool = False


class PrinterConfigParser:
    """Parse Klipper printer.cfg and extract capabilities."""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path
        self.config_text = ""
        if config_path and Path(config_path).exists():
            with open(config_path, 'r') as f:
                self.config_text = f.read()
    
    def parse(self) -> PrinterCapabilities:
        """Parse printer.cfg and extract capabilities."""
        caps = PrinterCapabilities()
        
        if not self.config_text:
            return caps  # Return defaults
        
        # Parse [printer] section
        printer_section = self._extract_section("printer")
        if printer_section:
            caps.max_velocity = self._get_float(printer_section, "max_velocity", caps.max_velocity)
            caps.max_accel = self._get_float(printer_section, "max_accel", caps.max_accel)
            caps.max_z_velocity = self._get_float(printer_section, "max_z_velocity", caps.max_z_velocity)
            caps.max_z_accel = self._get_float(printer_section, "max_z_accel", caps.max_z_accel)
        
        # Parse [stepper_x]
        stepper_x = self._extract_section("stepper_x")
        if stepper_x:
            caps.x_max = self._get_float(stepper_x, "position_max", caps.x_max)
            caps.x_min = self._get_float(stepper_x, "position_min", caps.x_min)
        
        # Parse [stepper_y]
        stepper_y = self._extract_section("stepper_y")
        if stepper_y:
            caps.y_max = self._get_float(stepper_y, "position_max", caps.y_max)
            caps.y_min = self._get_float(stepper_y, "position_min", caps.y_min)
        
        # Parse [stepper_z]
        stepper_z = self._extract_section("stepper_z")
        if stepper_z:
            caps.z_max = self._get_float(stepper_z, "position_max", caps.z_max)
            caps.z_min = self._get_float(stepper_z, "position_min", caps.z_min)
        
        # Parse [extruder]
        extruder = self._extract_section("extruder")
        if extruder:
            caps.nozzle_diameter = self._get_float(extruder, "nozzle_diameter", caps.nozzle_diameter)
            caps.filament_diameter = self._get_float(extruder, "filament_diameter", caps.filament_diameter)
            caps.max_temp = self._get_float(extruder, "max_temp", caps.max_temp)
            caps.min_temp = self._get_float(extruder, "min_temp", caps.min_temp)
            caps.max_extrude_only_velocity = self._get_float(extruder, "max_extrude_only_velocity", caps.max_extrude_only_velocity)
            caps.max_extrude_only_accel = self._get_float(extruder, "max_extrude_only_accel", caps.max_extrude_only_accel)
            caps.pressure_advance = self._get_float(extruder, "pressure_advance", None)
            caps.pressure_advance_smooth_time = self._get_float(extruder, "pressure_advance_smooth_time", None)
            caps.has_pressure_advance = caps.pressure_advance is not None
        
        # Parse [heater_bed]
        heater_bed = self._extract_section("heater_bed")
        if heater_bed:
            caps.bed_max_temp = self._get_float(heater_bed, "max_temp", caps.bed_max_temp)
        
        # Check for features
        caps.has_bltouch = "[bltouch]" in self.config_text.lower() or "[probe]" in self.config_text.lower()
        caps.has_input_shaper = "[input_shaper]" in self.config_text.lower()
        
        return caps
    
    def _extract_section(self, section_name: str) -> Optional[str]:
        """Extract a config section by name."""
        pattern = rf'\[{re.escape(section_name)}\](.*?)(?=\n\[|$)'
        match = re.search(pattern, self.config_text, re.DOTALL | re.IGNORECASE)
        return match.group(1) if match else None
    
    def _get_float(self, section_text: str, key: str, default: Optional[float]) -> Optional[float]:
        """Extract a float value from section text."""
        pattern = rf'{re.escape(key)}\s*[:=]\s*([0-9.]+)'
        match = re.search(pattern, section_text, re.IGNORECASE)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                return default
        return default
