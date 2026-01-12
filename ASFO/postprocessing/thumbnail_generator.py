"""
Standalone thumbnail generator for G-code files.
Based on Cura's CreateThumbnail.py but adapted for CLI use with matplotlib.
"""
import base64
import io
import struct
from pathlib import Path
from typing import Tuple, List

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import numpy as np


class ThumbnailGenerator:
    """Generate thumbnails from STL files and inject into G-code."""
    
    def __init__(self, sizes: List[Tuple[int, int]] = None):
        """
        Initialize thumbnail generator.
        
        Args:
            sizes: List of (width, height) tuples. Default: [(32, 32), (300, 300)]
        """
        self.sizes = sizes or [(32, 32), (300, 300)]
    
    @staticmethod
    def load_stl(stl_path: Path) -> np.ndarray:
        """Load STL file (binary or ASCII) and return vertices array."""
        with open(stl_path, 'rb') as f:
            header = f.read(80)
            
            # Check if ASCII STL (starts with "solid")
            if header.startswith(b'solid'):
                f.seek(0)
                vertices_list = []
                current_facet = []
                
                for line_bytes in f:
                    try:
                        line = line_bytes.decode('utf-8', errors='ignore').strip()
                    except:
                        continue
                        
                    if line.startswith('vertex'):
                        parts = line.split()
                        if len(parts) == 4:
                            vertex = [float(parts[1]), float(parts[2]), float(parts[3])]
                            current_facet.append(vertex)
                            
                            if len(current_facet) == 3:
                                vertices_list.append(current_facet)
                                current_facet = []
                
                if not vertices_list:
                    raise ValueError("No vertices found in ASCII STL")
                    
                return np.array(vertices_list, dtype=np.float32)
            else:
                # Binary STL
                count = struct.unpack('<I', f.read(4))[0]
                
                if count > 10000000:  # Sanity check
                    raise ValueError(f"STL file appears corrupted (claims {count} triangles)")
                
                dtype = np.dtype([
                    ('normal', '<f4', (3,)),
                    ('v1', '<f4', (3,)),
                    ('v2', '<f4', (3,)),
                    ('v3', '<f4', (3,)),
                    ('attr', '<u2')
                ])
                data = np.fromfile(f, dtype=dtype, count=count)
                
                vertices = np.empty((count, 3, 3))
                vertices[:, 0, :] = data['v1']
                vertices[:, 1, :] = data['v2']
                vertices[:, 2, :] = data['v3']
                return vertices
    
    @staticmethod
    def generate_image(vertices: np.ndarray, width: int, height: int) -> bytes:
        """Render isometric view of STL mesh to PNG bytes."""
        fig = plt.figure(figsize=(width/100, height/100), dpi=100)
        ax = fig.add_subplot(111, projection='3d')
        
        # Create mesh collection with better colors
        mesh = Poly3DCollection(vertices, alpha=0.95)
        mesh.set_facecolor('#FF6B35')  # Orange/coral color
        mesh.set_edgecolor('#1A1A1A')  # Dark edges
        mesh.set_linewidth(0.05)
        ax.add_collection3d(mesh)

        # Auto-scale
        all_points = vertices.reshape(-1, 3)
        min_vals = np.min(all_points, axis=0)
        max_vals = np.max(all_points, axis=0)
        center = (min_vals + max_vals) / 2
        
        # Center the plot
        max_range = np.max(max_vals - min_vals)
        ax.set_xlim(center[0] - max_range/2, center[0] + max_range/2)
        ax.set_ylim(center[1] - max_range/2, center[1] + max_range/2)
        ax.set_zlim(center[2] - max_range/2, center[2] + max_range/2)
        
        # Isometric view
        ax.view_init(elev=30, azim=45)
        
        # Remove axes and set transparent background
        ax.set_axis_off()
        ax.set_facecolor('none')
        fig.patch.set_alpha(0.0)
        plt.subplots_adjust(top=1, bottom=0, right=1, left=0, hspace=0, wspace=0)
        
        # Save to buffer with transparency
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=100, transparent=True,
                   bbox_inches='tight', pad_inches=0)
        plt.close(fig)
        buf.seek(0)
        return buf.read()
    
    def generate_thumbnails(self, stl_path: Path) -> List[Tuple[int, int, bytes]]:
        """
        Generate all configured thumbnail sizes from STL.
        
        Returns:
            List of (width, height, png_bytes) tuples
        """
        vertices = self.load_stl(stl_path)
        thumbnails = []
        
        for width, height in self.sizes:
            try:
                img_data = self.generate_image(vertices, width, height)
                thumbnails.append((width, height, img_data))
                print(f"Generated {width}x{height} thumbnail ({len(img_data)} bytes)")
            except Exception as e:
                print(f"Failed to generate {width}x{height} thumbnail: {e}")
                
        return thumbnails
    
    @staticmethod
    def create_gcode_block(width: int, height: int, png_data: bytes, 
                          chunk_size: int = 78) -> List[str]:
        """
        Convert PNG thumbnail to G-code comment block.
        
        Mainsail format: "; thumbnail begin WIDTHxHEIGHT SIZE"
        The header must NOT have extra spaces and must use lowercase 'thumbnail'
        """
        b64 = base64.b64encode(png_data).decode('ascii')
        
        gcode = [
            f"; thumbnail begin {width}x{height} {len(b64)}"
        ]
        
        # Chunk base64 into lines
        for i in range(0, len(b64), chunk_size):
            gcode.append(f"; {b64[i:i+chunk_size]}")
        
        gcode.append("; thumbnail end")
        gcode.append(";")
        
        return gcode
    
    def inject_into_gcode(self, gcode_path: Path, stl_path: Path) -> bool:
        """
        Inject thumbnails into G-code file.
        
        Inserts after CuraEngine headers, replacing the ;Generated line.
        Returns True if successful.
        """
        try:
            # Generate all thumbnails
            thumbnails = self.generate_thumbnails(stl_path)
            
            if not thumbnails:
                print("No thumbnails generated")
                return False
            
            # Build header block
            headers = [
                ";POSTPROCESSED",
                ";  [CreateThumbnail]",
                ";  [Cura_JPEG_Preview]",
                ";Generated with Cura_SteamEngine 4.13.0",
                ";"
            ]
            
            # Add all thumbnail blocks
            for width, height, png_data in thumbnails:
                headers.extend(self.create_gcode_block(width, height, png_data))
            
            # Read and modify G-code
            with open(gcode_path, 'r') as f:
                lines = f.readlines()
            
            # Find and replace ;Generated line
            generated_index = -1
            for i, line in enumerate(lines):
                if line.startswith(';Generated'):
                    generated_index = i
                    break
            
            if generated_index >= 0:
                # Replace ;Generated line with our header block
                new_lines = (lines[:generated_index] + 
                           [h + "\n" for h in headers] + 
                           lines[generated_index+1:])
            else:
                # Fallback: prepend if ;Generated not found
                print("WARNING: ;Generated line not found, prepending to file")
                new_lines = [h + "\n" for h in headers] + lines
            
            # Write back
            with open(gcode_path, 'w') as f:
                f.writelines(new_lines)
            
            print(f"SUCCESS: Injected {len(thumbnails)} thumbnails into {gcode_path}")
            return True
            
        except Exception as e:
            print(f"ERROR: Failed to inject thumbnails: {e}")
            import traceback
            traceback.print_exc()
            return False
