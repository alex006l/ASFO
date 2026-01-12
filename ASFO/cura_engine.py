"""CuraEngine wrapper and profile management."""
import json
import subprocess
import urllib.request
import ssl
from pathlib import Path
from typing import Dict, Any, Optional
from .config import CURAENGINE_PATH, PROFILES_DIR, GCODE_DIR
from .models import PrintProfile
from .postprocessing.thumbnail_generator import ThumbnailGenerator
from .postprocessing.klipper_preprocessor import process_gcode_for_klipper

FDMPRINTER_URL = "https://raw.githubusercontent.com/Ultimaker/Cura/4.13/resources/definitions/fdmprinter.def.json"
FDMEXTRUDER_URL = "https://raw.githubusercontent.com/Ultimaker/Cura/4.13/resources/definitions/fdmextruder.def.json"
DEFS_DIR = Path(__file__).parent / "definitions"
DEF_FILE = DEFS_DIR / "fdmprinter.def.json"
EXTRUDER_DEF_FILE = DEFS_DIR / "fdmextruder.def.json"

class CuraEngineWrapper:
    """Wrapper for CuraEngine CLI."""
    
    def __init__(self, curaengine_path: str = CURAENGINE_PATH):
        self.curaengine_path = curaengine_path
        self._ensure_definitions()

    def _ensure_definitions(self):
        """Ensure base definitions exist."""
        if not DEFS_DIR.exists():
            try:
                DEFS_DIR.mkdir(parents=True, exist_ok=True)
            except OSError:
                pass 
        
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        if not DEF_FILE.exists():
            print(f"Downloading base definition from {FDMPRINTER_URL}...")
            try:
                with urllib.request.urlopen(FDMPRINTER_URL, context=ctx) as response, open(DEF_FILE, 'wb') as out_file:
                    out_file.write(response.read())
            except Exception as e:
                print(f"Warning: Failed to download base definition: {e}")

        if not EXTRUDER_DEF_FILE.exists():
            print(f"Downloading extruder definition from {FDMEXTRUDER_URL}...")
            try:
                with urllib.request.urlopen(FDMEXTRUDER_URL, context=ctx) as response, open(EXTRUDER_DEF_FILE, 'wb') as out_file:
                    out_file.write(response.read())
            except Exception as e:
                print(f"Warning: Failed to download extruder definition: {e}")

    def generate_profile_json(self, profile: PrintProfile) -> Path:
        """Generate CuraEngine JSON config from profile."""
        settings = {
            "settings": {
                "machine_extruder_count": { "default_value": 1 },
                "machine_heated_bed": { "default_value": True },
                "machine_width": { "default_value": 220 },
                "machine_depth": { "default_value": 220 },
                "machine_height": { "default_value": 250 },
                "machine_center_is_zero": { "default_value": False },
                "machine_shape": { "default_value": "rectangular" },
                "machine_nozzle_size": { "default_value": 0.4 },
                "machine_filament_diameter": { "default_value": 1.75 },
                "mesh_rotation_matrix": { "label": "Mesh Rotation Matrix", "type": "str", "default_value": "[[1,0,0], [0,1,0], [0,0,1]]" },
                "mesh_position_x": { "label": "Mesh Rotation Matrix", "type": "float", "default_value": 0 },
                "mesh_position_y": { "label": "Mesh Position Y", "type": "float", "default_value": 0 },
                "mesh_position_z": { "label": "Mesh Position Z", "type": "float", "default_value": 0 },
                "center_object": { "label": "Center Object", "type": "bool", "default_value": True },
                "layer_height": { "default_value": profile.layer_height },
                "wall_thickness": { "default_value": profile.wall_thickness },
                "top_bottom_thickness": { "default_value": profile.top_bottom_thickness },
                "infill_sparse_density": { "default_value": profile.infill_density },
                "speed_print": { "default_value": profile.print_speed },
                "speed_travel": { "default_value": profile.travel_speed },
                "material_print_temperature": { "default_value": profile.nozzle_temp },
                "material_bed_temperature": { "default_value": profile.bed_temp },
                "retraction_amount": { "default_value": profile.retraction_distance },
                "retraction_speed": { "default_value": profile.retraction_speed },
                "material_flow": { "default_value": profile.extrusion_multiplier * 100 },
                "speed_layer_0": { "default_value": profile.first_layer_speed },
                "layer_height_0": { "default_value": profile.first_layer_height },
                "skirt_brim_minimal_length": { "default_value": 250 },
                "support_enable": { "default_value": False },
                "infill_before_walls": { "default_value": False },
            }
        }
        
        profile_file = PROFILES_DIR / f"profile_{profile.printer_id}_{profile.material}_v{profile.version}.json"
        with open(profile_file, "w") as f:
            json.dump(settings, f, indent=2)
        
        return profile_file
    
    def slice(self, stl_path: str, profile: PrintProfile, output_name: str, printer_capabilities: dict = None) -> Dict[str, Any]:
        profile_json = self.generate_profile_json(profile)
        output_path = GCODE_DIR / f"{output_name}.gcode"
        cmd = [str(self.curaengine_path), "slice"]
        
        # Load base definitions
        if DEF_FILE.exists():
            cmd.extend(["-j", str(DEF_FILE)])
        if EXTRUDER_DEF_FILE.exists():
            cmd.extend(["-j", str(EXTRUDER_DEF_FILE)])

        cmd.extend(["-j", str(profile_json), "-o", str(output_path), "-l", str(stl_path)])
        
        try:
            print(f"Running CuraEngine: {' '.join(str(x) for x in cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300, check=True)
            print(f"CuraEngine completed. Output file: {output_path}")
            
            # Inject thumbnails using post-processing
            try:
                print(f"Starting thumbnail injection...")
                thumbnail_gen = ThumbnailGenerator(sizes=[(32, 32), (300, 300)])
                thumbnail_gen.inject_into_gcode(output_path, Path(stl_path))
                print(f"Thumbnail injection completed successfully")
            except Exception as e:
                print(f"Warning: Thumbnail injection failed: {e}")
                import traceback
                traceback.print_exc()
            
            # Apply Klipper preprocessing
            try:
                print(f"Starting Klipper preprocessing...")
                process_gcode_for_klipper(
                    Path(output_path),
                    add_set_print_stats_info=True,
                    add_timelapse_take_frame=True,
                    add_moonraker_metadata=True
                )
                print(f"Klipper preprocessing completed successfully")
            except Exception as e:
                print(f"Warning: Klipper preprocessing failed: {e}")
                import traceback
                traceback.print_exc()

            estimated_time = self._parse_time_from_output(result.stdout)
            filament_length = self._parse_filament_from_output(result.stdout)
            print(f"Slicing complete: {output_path}")
            return {
                "gcode_path": str(output_path),
                "estimated_time_seconds": estimated_time,
                "filament_length_mm": filament_length,
                "filament_weight_g": filament_length * 0.0029 if filament_length else None
            }
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"CuraEngine failed (Exit {e.returncode}):\nSTDOUT: {e.stdout}\nSTDERR: {e.stderr}")
        except subprocess.TimeoutExpired:
            raise RuntimeError("CuraEngine timeout (>5min)")
    
    def _parse_time_from_output(self, output: str) -> int:
        for line in output.split("\n"):
            if "print time" in line.lower():
                try: return int(float(line.split(":")[1].strip()))
                except: pass
        return 3600
    
    def _parse_filament_from_output(self, output: str) -> Optional[float]:
        for line in output.split("\n"):
            if "filament" in line.lower() and "mm" in line.lower():
                try: 
                    import re; 
                    match=re.search(r"(\d+(\.\d+)?)", line)
                    if match: return float(match.group(1))
                except: pass
        return 1000.0
