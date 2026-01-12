"""Thumbnail generator for G-code."""
import base64
import io
import math
import struct
from pathlib import Path
from typing import Dict
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import numpy as np

class ThumbnailGenerator:
    """Generates thumbnails from STL and embeds in G-code."""

    @staticmethod
    def load_stl(stl_path):
        """Simple STL loader using numpy - handles both binary and ASCII STL."""
        with open(stl_path, 'rb') as f:
            header = f.read(80)
            
            # Check if it's an ASCII STL (starts with "solid")
            if header.startswith(b'solid'):
                print(f"Detected ASCII STL format")
                f.seek(0)
                # Parse ASCII STL
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
                    
                vertices = np.array(vertices_list, dtype=np.float32)
                print(f"Loaded {len(vertices)} triangles from ASCII STL")
                return vertices
            else:
                # Binary STL
                print(f"Detected binary STL format")
                count = struct.unpack('<I', f.read(4))[0]
                
                # Sanity check - if count is unreasonably large, it's probably corrupted
                if count > 10000000:  # 10 million triangles is already huge
                    raise ValueError(f"STL file appears corrupted (claims {count} triangles)")
                
                # STL format: normal (3f), v1 (3f), v2 (3f), v3 (3f), attr (2u) = 50 bytes
                dtype = np.dtype([
                    ('normal', '<f4', (3,)),
                    ('v1', '<f4', (3,)),
                    ('v2', '<f4', (3,)),
                    ('v3', '<f4', (3,)),
                    ('attr', '<u2')
                ])
                data = np.fromfile(f, dtype=dtype, count=count)
                
                # Extract vertices
                vertices = np.empty((count, 3, 3))
                vertices[:, 0, :] = data['v1']
                vertices[:, 1, :] = data['v2']
                vertices[:, 2, :] = data['v3']
                print(f"Loaded {len(vertices)} triangles from binary STL")
                return vertices

    @staticmethod
    def generate_image(vertices, width=300, height=300):
        """Render isometric view to buffer."""
        print(f"Generating {width}x{height} thumbnail...")
        try:
            fig = plt.figure(figsize=(width/100, height/100), dpi=100)
            ax = fig.add_subplot(111, projection='3d')
            
            # Create mesh collection
            mesh = Poly3DCollection(vertices, alpha=0.8)
            mesh.set_facecolor('#00bcd4')
            mesh.set_edgecolor('#008ba3')
            mesh.set_linewidth(0.1)
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
            
            # Remove axes
            ax.set_axis_off()
            plt.subplots_adjust(top=1, bottom=0, right=1, left=0, hspace=0, wspace=0)
            
            # Save to buffer
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=100, facecolor='#252525', bbox_inches='tight', pad_inches=0)
            plt.close(fig)
            buf.seek(0)
            data = buf.read()
            print(f"Generated {width}x{height} thumbnail: {len(data)} bytes")
            return data
        except Exception as e:
            print(f"Error generating {width}x{height} image: {e}")
            plt.close('all')  # Clean up any open figures
            raise

    @staticmethod
    def inject_thumbnail(gcode_path: Path, stl_path: Path):
        """Generate thumbnail and inject into G-code."""
        print(f"\n=== THUMBNAIL INJECTION START ===")
        print(f"G-code path: {gcode_path}")
        print(f"STL path: {stl_path}")
        print(f"G-code exists: {gcode_path.exists()}")
        print(f"STL exists: {stl_path.exists()}")
        
        try:
            print(f"Loading STL file...")
            vertices = ThumbnailGenerator.load_stl(stl_path)
            print(f"Loaded {len(vertices)} triangles from STL")
            
            # Generate thumbnails - Mainsail standard sizes
            # Small (50x50) for file list, Large (300x300 or 400x400) for preview
            images = []
            for w, h in [(32, 32), (300, 300)]:
                try:
                    img_data = ThumbnailGenerator.generate_image(vertices, w, h)
                    images.append((w, h, img_data))
                except Exception as e:
                    print(f"Failed to generate {w}x{h} image: {e}")
                    import traceback
                    traceback.print_exc()
            
            if not images:
                print("ERROR: No images were generated successfully")
                return
            
            print(f"Building thumbnail headers...")
            headers = []
            headers.append(";POSTPROCESSED")
            headers.append(";  [CreateThumbnail]")
            headers.append(";  [Cura_JPEG_Preview]")
            headers.append(";Generated with Cura_SteamEngine 4.13.0")
            headers.append(";")

            for w, h, data in images:
                b64 = base64.b64encode(data).decode('utf-8')
                print(f"Encoded {w}x{h} to {len(b64)} base64 chars")
                headers.append(f"; jpeg thumbnail begin {w}x{h} {len(data)}")
                # Chunk base64 string
                for i in range(0, len(b64), 78):
                    headers.append(f"; {b64[i:i+78]}")
                headers.append("; thumbnail end")
                headers.append(";")
            
            print(f"Reading existing G-code from {gcode_path}...")
            with open(gcode_path, 'r') as f:
                lines = f.readlines()
            print(f"Read {len(lines)} lines of G-code")
            
            # Find and replace the ;Generated line
            generated_index = -1
            for i, line in enumerate(lines):
                if line.startswith(';Generated'):
                    generated_index = i
                    break
            
            if generated_index >= 0:
                print(f"Replacing ;Generated line at index {generated_index}")
                # Remove the original ;Generated line and insert our headers
                new_lines = lines[:generated_index] + [line + "\n" for line in headers] + lines[generated_index+1:]
            else:
                # Fallback: insert at beginning if ;Generated not found
                print("WARNING: ;Generated line not found, inserting at beginning")
                new_lines = [line + "\n" for line in headers] + lines
            
            print(f"New content: {len(new_lines)} lines")
            
            print(f"Writing updated G-code...")
            with open(gcode_path, 'w') as f:
                f.writelines(new_lines)
            print(f"File written successfully")
                
            print(f"SUCCESS: Thumbnails injected into {gcode_path}")
            print(f"=== THUMBNAIL INJECTION END ===\n")
            
        except Exception as e:
            print(f"ERROR: Failed to inject thumbnail: {e}")
            import traceback
            traceback.print_exc()
            print(f"=== THUMBNAIL INJECTION FAILED ===\n")
    
    @staticmethod
    def extract_thumbnails_from_gcode(gcode_path: Path) -> Dict[str, str]:
        """
        Extract thumbnails embedded in G-code (from Cura's CreateThumbnail script).
        Returns dict with sizes as keys (e.g., '32x32', '400x400') and base64 data as values.
        """
        thumbnails = {}
        try:
            with open(gcode_path, 'r') as f:
                current_thumb = None
                current_size = None
                thumb_data = []
                
                for line in f:
                    line = line.strip()
                    
                    # Check for thumbnail begin
                    if "thumbnail begin" in line:
                        parts = line.split()
                        # Find the part that looks like WxH
                        for part in parts:
                            if 'x' in part and part.replace('x','').isdigit():
                                current_size = part
                                current_thumb = True
                                thumb_data = []
                                break
                    
                    # Check for thumbnail end
                    elif line.startswith("; thumbnail end"):
                        if current_thumb and current_size:
                            # Join all base64 chunks
                            b64_data = ''.join(thumb_data)
                            thumbnails[current_size] = b64_data
                        current_thumb = None
                        current_size = None
                        thumb_data = []
                    
                    # Collect base64 data
                    elif current_thumb and line.startswith(";"):
                        # Remove leading "; " and collect data
                        # Some formats have "; " others just ";"
                        data_part = line[1:].strip()
                        if data_part and not data_part.startswith("thumbnail"): # Avoid grabbing headers
                             thumb_data.append(data_part)
        except Exception as e:
            print(f"Error extracting thumbnails: {e}")
        return thumbnails
