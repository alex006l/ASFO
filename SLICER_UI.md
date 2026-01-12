# ASFO Slicer UI Features

## Thumbnail Generation

G-code files now include embedded thumbnails automatically generated during the slicing process. This feature integrates Cura's Create Thumbnail post-processing script.

### Implementation Details

**CuraEngine Configuration** (`cura_engine.py`)
- Added post-processing scripts to the profile JSON configuration
- Two thumbnail sizes are generated:
  - **32x32**: Small preview for list views
  - **400x400**: Large detailed preview for modal/expanded views

```python
"post_processing_scripts": [
    {
        "script": "CreateThumbnail",
        "parameters": {
            "width": 32,
            "height": 32
        }
    },
    {
        "script": "CreateThumbnail",
        "parameters": {
            "width": 400,
            "height": 400
        }
    }
]
```

**Thumbnail Extraction** (`thumbnail.py`)
- Added `extract_thumbnails_from_gcode()` method to parse thumbnails from G-code comments
- Thumbnails are stored as base64-encoded PNG data in the G-code header
- Format: `; thumbnail begin <size> <bytes>` followed by base64 chunks and `; thumbnail end`

**API Endpoint** (`app.py`)
- New endpoint: `GET /gcode-thumbnails/{gcode_filename}`
- Returns JSON with thumbnail data for each size
- Example response:
```json
{
  "filename": "model_PLA_1.gcode",
  "thumbnails": {
    "32x32": "iVBORw0KGgo...",
    "400x400": "iVBORw0KGgo..."
  },
  "count": 2
}
```

**UI Integration** (`index.html`)
- Thumbnails are automatically fetched and displayed in the jobs list after slicing
- Falls back gracefully if thumbnails are not available

---

## 3D Model Viewer

A full-featured 3D viewer has been added to the web interface, providing basic slicer functionality with real-time model manipulation.

### Features

#### 🎨 Interactive 3D Rendering
- **STL File Loading**: Automatically loads and displays STL files when selected
- **Real-time Rendering**: Powered by Three.js with WebGL acceleration
- **Camera Controls**: Orbit, pan, and zoom with mouse/touch
- **Visual Aids**:
  - Grid helper (200mm grid)
  - Axes helper (X/Y/Z indicators)
  - Proper lighting (ambient + directional)

#### 🎯 Transform Controls

**Position** (X, Y, Z in millimeters)
- Numeric inputs for precise placement
- Real-time position updates in the 3D view
- Useful for multi-object layouts or specific placement needs

**Rotation** (X, Y, Z in degrees, 0-360°)
- Dual input: sliders for quick adjustment + number inputs for precision
- Real-time rotation preview
- Perfect for orienting models for optimal printing

**Scale** (X, Y, Z multiplier, 0.1-3.0)
- Independent scaling on each axis
- Dual input: sliders + number inputs
- Live preview of scaled model
- Useful for resizing models or creating non-uniform scaling effects

#### 🔧 Utility Functions

**Reset Transforms**
- Resets position to (0, 0, 0)
- Resets rotation to (0°, 0°, 0°)
- Resets scale to (1, 1, 1)
- One-click return to default state

**Center Model**
- Moves model to build plate center
- Resets X and Y position to 0
- Maintains Z position and other transforms

**Fit to View**
- Automatically adjusts camera distance and position
- Frames the entire model in the viewport
- Useful after scaling or when model is out of view

### Technical Implementation

**Libraries Used**
- **Three.js 0.150.1**: 3D rendering engine
- **STLLoader**: Binary STL file parsing
- **OrbitControls**: Interactive camera controls

**Key Components**

1. **Scene Setup**
   - Dark background (#0d0d0d) matching UI theme
   - Perspective camera with 45° FOV
   - WebGL renderer with antialiasing

2. **Model Loading**
   - FileReader API for client-side file reading
   - STLLoader parses binary STL geometry
   - Automatic centering on Z=0 (build plate)
   - Material: Phong shading with cyan color (#00bcd4)

3. **Transform System**
   - Direct mesh manipulation via Three.js
   - Bidirectional sync between sliders and inputs
   - Degree-to-radian conversion for rotations
   - Real-time updates on every input change

4. **Responsive Design**
   - Adapts to container width
   - Window resize handling
   - Mobile-friendly touch controls (via OrbitControls)

### Usage Workflow

1. **Upload STL File**
   - Drag & drop or click to browse
   - File is automatically loaded into 3D viewer
   - Viewer card appears with model rendered

2. **Adjust Model** (Optional)
   - Use position controls to move model on build plate
   - Rotate model for optimal printing orientation
   - Scale model if size adjustment needed

3. **Slice**
   - Click "Upload & Slice" button
   - Current transform settings are used (if you want to apply them to slicing in the future)
   - G-code is generated with embedded thumbnails

4. **Review Results**
   - Sliced job appears in jobs list with thumbnail preview
   - Download G-code or start print directly

### Future Enhancements

Potential improvements for the 3D viewer:

- [ ] Apply transform settings to actual slicing (modify mesh before sending to CuraEngine)
- [ ] Multiple model support (arrange multiple STLs on build plate)
- [ ] Support detection and visualization
- [ ] Build volume boundary visualization
- [ ] Collision detection between models
- [ ] Layer preview after slicing
- [ ] Measurement tools
- [ ] Model statistics (dimensions, volume, estimated weight)
- [ ] Save/load viewport presets
- [ ] Export transformed STL

### Browser Compatibility

The 3D viewer requires a modern browser with WebGL support:
- ✅ Chrome/Edge 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Opera 76+

---

## Files Modified

- `ASFO/cura_engine.py` - Added post-processing script configuration
- `ASFO/thumbnail.py` - Added thumbnail extraction method
- `ASFO/app.py` - Added `/gcode-thumbnails/{filename}` endpoint
- `ASFO/static/index.html` - Added 3D viewer UI and functionality

## Testing

To test the new features:

1. **Start ASFO service**: `python -m ASFO.app`
2. **Open web UI**: Navigate to `http://localhost:5000/ui/index.html`
3. **Upload an STL file**: The 3D viewer should appear and render the model
4. **Adjust transforms**: Try position, rotation, and scale controls
5. **Slice the model**: Click "Upload & Slice"
6. **Verify thumbnails**: Check that the jobs list shows thumbnail preview
7. **Test API**: `curl http://localhost:5000/gcode-thumbnails/{filename}.gcode`

## Notes

- Thumbnails are embedded in G-code comments and compatible with Mainsail/Fluidd
- The 3D viewer runs entirely in the browser (no server-side rendering)
- Transform settings in the UI are currently for preview only; they don't modify the actual slicing geometry (yet)
- Large STL files may take a few seconds to load and render
