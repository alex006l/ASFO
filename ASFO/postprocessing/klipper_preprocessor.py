"""
CLI-compatible Klipper Preprocessor for G-code files.
Adapted from pedrolamas/klipper-preprocessor for use without Cura GUI.
"""
from pathlib import Path
from typing import List, Tuple


class KlipperPreprocessor:
    """Klipper-specific G-code post-processor."""
    
    def __init__(
        self,
        add_set_print_stats_info: bool = True,
        add_timelapse_take_frame: bool = True,
        add_moonraker_metadata: bool = True
    ):
        """
        Initialize Klipper preprocessor.
        
        Args:
            add_set_print_stats_info: Add SET_PRINT_STATS_INFO for layer tracking
            add_timelapse_take_frame: Add TIMELAPSE_TAKE_FRAME for timelapses
            add_moonraker_metadata: Add extra metadata comments for Moonraker
        """
        self.add_set_print_stats_info = add_set_print_stats_info
        self.add_timelapse_take_frame = add_timelapse_take_frame
        self.add_moonraker_metadata = add_moonraker_metadata
    
    def process(self, gcode_path: Path) -> None:
        """
        Process G-code file in place with Klipper enhancements.
        
        Args:
            gcode_path: Path to G-code file to process
        """
        print(f"Klipper preprocessing: {gcode_path}")
        
        # Read original content
        with open(gcode_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Process lines
        total_layers = self._count_layers(lines)
        processed_lines = self._process_lines(lines, total_layers)
        
        # Write back
        with open(gcode_path, 'w', encoding='utf-8') as f:
            f.writelines(processed_lines)
        
        print(f"Klipper preprocessing complete: {total_layers} layers")
    
    def _count_layers(self, lines: List[str]) -> int:
        """Count total layers in G-code."""
        count = 0
        for line in lines:
            if line.startswith(';LAYER:'):
                count += 1
        return count
    
    def _process_lines(self, lines: List[str], total_layers: int) -> List[str]:
        """
        Process G-code lines with Klipper enhancements.
        
        Args:
            lines: Original G-code lines
            total_layers: Total layer count
            
        Returns:
            Processed G-code lines
        """
        output = []
        current_layer = 0
        in_start_gcode = True
        metadata_added = False
        
        for line in lines:
            # Add Moonraker metadata after initial comments
            if self.add_moonraker_metadata and in_start_gcode and not metadata_added:
                if line.startswith(';Generated') or line.startswith('G'):
                    # Insert metadata before first G-code command
                    output.extend(self._get_moonraker_metadata())
                    metadata_added = True
                    in_start_gcode = False
            
            # Handle layer changes
            if line.startswith(';LAYER:'):
                current_layer += 1
                output.append(line)
                
                # Add SET_PRINT_STATS_INFO for current layer
                if self.add_set_print_stats_info:
                    output.append(f"SET_PRINT_STATS_INFO CURRENT_LAYER={current_layer}\n")
                
                # Add TIMELAPSE_TAKE_FRAME for timelapse
                if self.add_timelapse_take_frame:
                    output.append("TIMELAPSE_TAKE_FRAME\n")
                
                continue
            
            # Handle layer count comment
            if line.startswith(';LAYER_COUNT:') and self.add_set_print_stats_info:
                output.append(line)
                output.append(f"SET_PRINT_STATS_INFO TOTAL_LAYER={total_layers}\n")
                continue
            
            # Default: keep line as-is
            output.append(line)
        
        return output
    
    def _get_moonraker_metadata(self) -> List[str]:
        """
        Get Moonraker metadata comment lines.
        
        These are comment lines that Moonraker parses for file metadata.
        Values will be filled in by CuraEngine output.
        """
        return [
            ";Klipper-enhanced G-code\n",
            ";Nozzle diameter = (from profile)\n",
            ";Filament type = (from profile)\n",
            ";Filament name = (from profile)\n",
        ]


def process_gcode_for_klipper(
    gcode_path: Path,
    add_set_print_stats_info: bool = True,
    add_timelapse_take_frame: bool = True,
    add_moonraker_metadata: bool = True
) -> None:
    """
    Convenience function to process G-code file for Klipper.
    
    Args:
        gcode_path: Path to G-code file
        add_set_print_stats_info: Add layer tracking macros
        add_timelapse_take_frame: Add timelapse frame capture
        add_moonraker_metadata: Add metadata comments
    """
    preprocessor = KlipperPreprocessor(
        add_set_print_stats_info=add_set_print_stats_info,
        add_timelapse_take_frame=add_timelapse_take_frame,
        add_moonraker_metadata=add_moonraker_metadata
    )
    preprocessor.process(gcode_path)
