"""Generate calibration test prints for specific filaments."""
from typing import Dict, Any, Optional
from pathlib import Path
from .printer_config import PrinterCapabilities
from .config import GCODE_DIR


class CalibrationPrintGenerator:
    """Generate G-code for calibration test prints."""
    
    def __init__(self, capabilities: PrinterCapabilities):
        self.caps = capabilities
    
    def generate_pressure_advance_test(
        self,
        start_pa: float = 0.0,
        end_pa: float = 0.1,
        steps: int = 10,
        nozzle_temp: float = 200.0,
        bed_temp: float = 60.0,
        print_speed: float = 100.0
    ) -> str:
        """
        Generate pressure advance calibration tower.
        
        Prints a tower with increasing PA values.
        Each section is labeled with PA value.
        """
        gcode_lines = []
        
        # Header
        gcode_lines.append("; Pressure Advance Calibration Test")
        gcode_lines.append(f"; Start PA: {start_pa}")
        gcode_lines.append(f"; End PA: {end_pa}")
        gcode_lines.append(f"; Steps: {steps}")
        gcode_lines.append("")
        
        # Start sequence
        gcode_lines.extend(self._generate_start_gcode(nozzle_temp, bed_temp))
        
        # Calculate PA step size
        pa_step = (end_pa - start_pa) / steps
        layer_height = 0.2
        section_height = 5.0  # mm per PA value
        
        # Generate tower sections
        current_z = layer_height
        for i in range(steps):
            current_pa = start_pa + (i * pa_step)
            gcode_lines.append(f"; Section {i+1}: PA = {current_pa:.4f}")
            gcode_lines.append(f"SET_PRESSURE_ADVANCE ADVANCE={current_pa:.4f}")
            gcode_lines.append("")
            
            # Print section (5mm tall)
            section_layers = int(section_height / layer_height)
            for layer in range(section_layers):
                gcode_lines.extend(self._generate_test_pattern_layer(
                    z=current_z,
                    speed=print_speed,
                    layer_height=layer_height
                ))
                current_z += layer_height
        
        # End sequence
        gcode_lines.extend(self._generate_end_gcode())
        
        return "\n".join(gcode_lines)
    
    def generate_flow_calibration_cube(
        self,
        nozzle_temp: float = 200.0,
        bed_temp: float = 60.0,
        flow_multiplier: float = 1.0
    ) -> str:
        """Generate a 20mm calibration cube for flow testing."""
        gcode_lines = []
        
        gcode_lines.append("; Flow Calibration Cube")
        gcode_lines.append(f"; Flow multiplier: {flow_multiplier}")
        gcode_lines.append("")
        
        gcode_lines.extend(self._generate_start_gcode(nozzle_temp, bed_temp))
        
        # Simple 20x20x20mm cube
        cube_size = 20.0
        layer_height = 0.2
        num_layers = int(cube_size / layer_height)
        
        # Center the cube
        x_center = (self.caps.x_max - self.caps.x_min) / 2
        y_center = (self.caps.y_max - self.caps.y_min) / 2
        x_start = x_center - (cube_size / 2)
        y_start = y_center - (cube_size / 2)
        
        gcode_lines.append(f"M221 S{int(flow_multiplier * 100)}  ; Set flow")
        gcode_lines.append("")
        
        for layer in range(num_layers):
            z = layer_height * (layer + 1)
            gcode_lines.append(f"; Layer {layer + 1}")
            gcode_lines.append(f"G0 Z{z:.3f}")
            
            # Draw square perimeter
            gcode_lines.append(f"G0 X{x_start:.3f} Y{y_start:.3f}")
            gcode_lines.append(f"G1 X{x_start + cube_size:.3f} Y{y_start:.3f} E0.8")
            gcode_lines.append(f"G1 X{x_start + cube_size:.3f} Y{y_start + cube_size:.3f} E0.8")
            gcode_lines.append(f"G1 X{x_start:.3f} Y{y_start + cube_size:.3f} E0.8")
            gcode_lines.append(f"G1 X{x_start:.3f} Y{y_start:.3f} E0.8")
        
        gcode_lines.extend(self._generate_end_gcode())
        
        return "\n".join(gcode_lines)
    
    def generate_temperature_tower(
        self,
        start_temp: float = 190.0,
        end_temp: float = 220.0,
        temp_step: float = 5.0,
        bed_temp: float = 60.0
    ) -> str:
        """Generate temperature tower test."""
        gcode_lines = []
        
        gcode_lines.append("; Temperature Tower Calibration")
        gcode_lines.append(f"; Start temp: {start_temp}°C")
        gcode_lines.append(f"; End temp: {end_temp}°C")
        gcode_lines.append(f"; Step: {temp_step}°C")
        gcode_lines.append("")
        
        gcode_lines.extend(self._generate_start_gcode(start_temp, bed_temp))
        
        layer_height = 0.2
        section_height = 10.0  # 10mm per temperature
        current_z = layer_height
        current_temp = start_temp
        
        while current_temp <= end_temp:
            gcode_lines.append(f"; Section: {current_temp}°C")
            gcode_lines.append(f"M104 S{current_temp:.0f}")
            gcode_lines.append("")
            
            section_layers = int(section_height / layer_height)
            for layer in range(section_layers):
                gcode_lines.extend(self._generate_test_pattern_layer(
                    z=current_z,
                    speed=50.0,
                    layer_height=layer_height
                ))
                current_z += layer_height
            
            current_temp += temp_step
        
        gcode_lines.extend(self._generate_end_gcode())
        
        return "\n".join(gcode_lines)
    
    def _generate_start_gcode(self, nozzle_temp: float, bed_temp: float) -> list:
        """Generate standard start G-code."""
        return [
            "; Start G-code",
            "G28  ; Home all axes",
            f"M190 S{bed_temp:.0f}  ; Wait for bed temp",
            f"M109 S{nozzle_temp:.0f}  ; Wait for nozzle temp",
            "G92 E0  ; Reset extruder",
            "G1 Z2.0 F3000  ; Move Z up",
            "G1 X10 Y10 F5000  ; Move to start position",
            "G1 Z0.3 F3000  ; Lower nozzle",
            "G1 X100 E15 F1000  ; Prime line",
            "G92 E0  ; Reset extruder",
            "G1 Z1.0 F3000  ; Lift nozzle",
            ""
        ]
    
    def _generate_end_gcode(self) -> list:
        """Generate standard end G-code."""
        return [
            "",
            "; End G-code",
            "G91  ; Relative positioning",
            "G1 E-2 F2700  ; Retract",
            "G1 Z10 F3000  ; Raise Z",
            "G90  ; Absolute positioning",
            "G1 X0 Y200 F3000  ; Present print",
            "M106 S0  ; Turn off fan",
            "M104 S0  ; Turn off hotend",
            "M140 S0  ; Turn off bed",
            "M84  ; Disable motors",
            "; Print complete!"
        ]
    
    def _generate_test_pattern_layer(
        self,
        z: float,
        speed: float,
        layer_height: float
    ) -> list:
        """Generate a single layer test pattern."""
        # Simple square pattern for testing
        x_center = (self.caps.x_max - self.caps.x_min) / 2
        y_center = (self.caps.y_max - self.caps.y_min) / 2
        size = 30.0
        
        return [
            f"G0 Z{z:.3f} F300",
            f"G0 X{x_center - size/2:.2f} Y{y_center - size/2:.2f} F{speed*60:.0f}",
            f"G1 X{x_center + size/2:.2f} E1.2",
            f"G1 Y{y_center + size/2:.2f} E1.2",
            f"G1 X{x_center - size/2:.2f} E1.2",
            f"G1 Y{y_center - size/2:.2f} E1.2",
        ]
    
    def save_calibration_print(self, gcode: str, name: str) -> str:
        """Save calibration G-code to file."""
        filepath = GCODE_DIR / f"calibration_{name}.gcode"
        with open(filepath, 'w') as f:
            f.write(gcode)
        return str(filepath)
