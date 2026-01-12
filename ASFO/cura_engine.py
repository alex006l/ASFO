"""CuraEngine wrapper and profile management."""
import json
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional
from .config import CURAENGINE_PATH, PROFILES_DIR, GCODE_DIR
from .models import PrintProfile


class CuraEngineWrapper:
    """Wrapper for CuraEngine CLI."""
    
    def __init__(self, curaengine_path: str = CURAENGINE_PATH):
        self.curaengine_path = curaengine_path
    
    def generate_profile_json(self, profile: PrintProfile) -> Path:
        """Generate CuraEngine JSON config from profile."""
        # Simplified CuraEngine settings
        # In production, use full fdmprinter.def.json base + overrides
        settings = {
            "settings": {

                # Machine Settings
                "machine_extruder_count": { "label": "Extruder Count", "type": "int", "default_value": 1 },
                "machine_heated_bed": { "label": "Heated Bed", "type": "bool", "default_value": True },
                "machine_width": { "label": "Machine Width", "type": "float", "default_value": 220 },
                "machine_depth": { "label": "Machine Depth", "type": "float", "default_value": 220 },
                "machine_height": { "label": "Machine Height", "type": "float", "default_value": 250 },
                "machine_center_is_zero": { "label": "Center Zero", "type": "bool", "default_value": False },
                "machine_shape": { "label": "Shape", "type": "str", "default_value": "rectangular" },
                "machine_nozzle_size": { "label": "Nozzle Size", "type": "float", "default_value": 0.4 },
                "machine_filament_diameter": { "label": "Filament Diameter", "type": "float", "default_value": 1.75 },
                
                # Mesh settings required by CuraEngine
                "mesh_rotation_matrix": { "label": "Mesh Rotation Matrix", "type": "str", "default_value": "[[1,0,0], [0,1,0], [0,0,1]]" },
                "mesh_position_x": { "label": "Mesh Position X", "type": "float", "default_value": 0 },
                "mesh_position_y": { "label": "Mesh Position Y", "type": "float", "default_value": 0 },
                "mesh_position_z": { "label": "Mesh Position Z", "type": "float", "default_value": 0 },
                "center_object": { "label": "Center Object", "type": "bool", "default_value": True },
                
                # Extrusion Settings
                "layer_height": { "label": "Layer Height", "type": "float", "default_value": profile.layer_height },
                "wall_thickness": { "label": "Wall Thickness", "type": "float", "default_value": profile.wall_thickness },
                "top_bottom_thickness": { "label": "Top/Bottom Thickness", "type": "float", "default_value": profile.top_bottom_thickness },
                "infill_sparse_density": { "label": "Infill Density", "type": "float", "default_value": profile.infill_density },
                "speed_print": { "label": "Print Speed", "type": "float", "default_value": profile.print_speed },
                "speed_travel": { "label": "Travel Speed", "type": "float", "default_value": profile.travel_speed },
                "material_print_temperature": { "label": "Nozzle Temperature", "type": "float", "default_value": profile.nozzle_temp },
                "material_bed_temperature": { "label": "Bed Temperature", "type": "float", "default_value": profile.bed_temp },
                "retraction_amount": { "label": "Retraction Amount", "type": "float", "default_value": profile.retraction_distance },
                "retraction_speed": { "label": "Retraction Speed", "type": "float", "default_value": profile.retraction_speed },
                "material_flow": { "label": "Material Flow", "type": "float", "default_value": profile.extrusion_multiplier * 100 },
                "speed_layer_0": { "label": "Initial Layer Speed", "type": "float", "default_value": profile.first_layer_speed },
                "layer_height_0": { "label": "Initial Layer Height", "type": "float", "default_value": profile.first_layer_height },
                
                # Dependencies that prevent errors
                "skirt_brim_minimal_length": { "label": "Skirt/Brim Min Length", "type": "float", "default_value": 250 },
                "support_enable": { "label": "Enable Support", "type": "bool", "default_value": False },
                "infill_before_walls": { "label": "Infill Before Walls", "type": "bool", "default_value": False },
            }
        }
        
        profile_file = PROFILES_DIR / f"profile_{profile.printer_id}_{profile.material}_v{profile.version}.json"
        with open(profile_file, "w") as f:
            json.dump(settings, f, indent=2)
        
        return profile_file
    
    def slice(self, stl_path: str, profile: PrintProfile, output_name: str) -> Dict[str, Any]:
        """
        Slice STL file using CuraEngine.
        
        Returns dict with:
        - gcode_path: path to generated gcode
        - estimated_time: seconds
        - filament_length: mm
        """
        profile_json = self.generate_profile_json(profile)
        output_path = GCODE_DIR / f"{output_name}.gcode"
        
        # CuraEngine command
        # Note: Actual CuraEngine requires more complete settings
        # This is a simplified example
        cmd = [
            str(self.curaengine_path),
            "slice",
            "-j", str(profile_json),
            "-o", str(output_path),
            "-l", str(stl_path)
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 min timeout
                check=True
            )
            
            # Parse output for metadata (CuraEngine prints this)
            estimated_time = self._parse_time_from_output(result.stdout)
            filament_length = self._parse_filament_from_output(result.stdout)
            
            return {
                "gcode_path": str(output_path),
                "estimated_time_seconds": estimated_time,
                "filament_length_mm": filament_length,
                "filament_weight_g": filament_length * 0.0029 if filament_length else None  # ~1.24g/m for PLA
            }
        
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"CuraEngine failed: {e.stderr}")
        except subprocess.TimeoutExpired:
            raise RuntimeError("CuraEngine timeout (>5min)")
    
    def _parse_time_from_output(self, output: str) -> int:
        """Parse estimated time from CuraEngine output."""
        # CuraEngine outputs "Print time: X" in various formats
        # This is a placeholder - adjust based on actual output
        for line in output.split("\n"):
            if "print time" in line.lower():
                # Extract seconds (rough estimation)
                return 3600  # placeholder
        return 3600  # default 1 hour
    
    def _parse_filament_from_output(self, output: str) -> Optional[float]:
        """Parse filament usage from CuraEngine output."""
        # Placeholder - parse actual CuraEngine output
        for line in output.split("\n"):
            if "filament" in line.lower():
                return 1000.0  # placeholder mm
        return None
