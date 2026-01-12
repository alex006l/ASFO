"""Thumbnail generator for G-code."""
import base64
import io
import math
import struct
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import numpy as np

class ThumbnailGenerator:
    """Generates thumbnails from STL and embeds in G-code."""

    @staticmethod
    def load_stl(stl_path):
        """Simple STL loader using numpy."""
        with open(stl_path, 'rb') as f:
            header = f.read(80)
            count = struct.unpack('<I', f.read(4))[0]
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
            return vertices

    @staticmethod
    def generate_image(vertices, width=300, height=300):
        """Render isometric view to buffer."""
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
        plt.savefig(buf, format='png', transparent=False, facecolor='#252525')
        plt.close(fig)
        buf.seek(0)
        return buf.read()

    @staticmethod
    def inject_thumbnail(gcode_path: Path, stl_path: Path):
        """Generate thumbnail and inject into G-code."""
        try:
            vertices = ThumbnailGenerator.load_stl(stl_path)
            
            # Generate 32x32 (mini) and 300x300 (large)
            images = [
                (32, 32, ThumbnailGenerator.generate_image(vertices, 32, 32)),
                (300, 300, ThumbnailGenerator.generate_image(vertices, 300, 300))
            ]
            
            headers = []
            for w, h, data in images:
                b64 = base64.b64encode(data).decode('utf-8')
                headers.append(f"; thumbnail begin {w}x{h} {len(data)}")
                # Chunk base64 string
                for i in range(0, len(b64), 78):
                    headers.append(f"; {b64[i:i+78]}")
                headers.append("; thumbnail end")
                headers.append("")
            
            # Read existing G-code
            with open(gcode_path, 'r') as f:
                content = f.read()
            
            # Prepend headers
            new_content = "\n".join(headers) + "\n" + content
            
            with open(gcode_path, 'w') as f:
                f.write(new_content)
                
            print(f"Thumbnails injected into {gcode_path}")
            
        except Exception as e:
            print(f"Failed to generate thumbnail: {e}")
