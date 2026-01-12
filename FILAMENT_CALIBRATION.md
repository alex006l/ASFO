# Filament Calibration Guide

## Overview

The slicer service now supports **filament-specific calibration** that goes beyond just material type (PLA, PETG, etc.). You can calibrate and save profiles for specific filament brands, colors, and spools, including Klipper-specific parameters like **pressure advance**.

## Why Filament-Specific Calibration?

Different filaments, even of the same material type, can behave differently:
- **Esun PLA+ Red** vs **Hatchbox PLA Black** — different optimal temperatures
- **Brand variations** — flow rates can vary by ±5%
- **Color pigments** — affect temperature and flow
- **Pressure advance** — varies significantly between filaments

## Workflow

### 1. Generate Calibration Prints

Generate test prints for each new filament:

```bash
# Pressure advance test
curl -X POST http://localhost:8080/calibration/generate \
  -H "Content-Type: application/json" \
  -d '{
    "printer_id": "ender3_01",
    "calibration_type": "pressure_advance",
    "filament_name": "esun_pla_red",
    "material_type": "PLA",
    "nozzle_temp": 200,
    "bed_temp": 60,
    "start_pa": 0.0,
    "end_pa": 0.1
  }'

# Flow calibration
curl -X POST http://localhost:8080/calibration/generate \
  -H "Content-Type: application/json" \
  -d '{
    "printer_id": "ender3_01",
    "calibration_type": "flow",
    "filament_name": "esun_pla_red",
    "material_type": "PLA",
    "nozzle_temp": 200,
    "bed_temp": 60,
    "flow_multiplier": 1.0
  }'

# Temperature tower
curl -X POST http://localhost:8080/calibration/generate \
  -H "Content-Type: application/json" \
  -d '{
    "printer_id": "ender3_01",
    "calibration_type": "temperature",
    "filament_name": "esun_pla_red",
    "material_type": "PLA",
    "start_temp": 190,
    "end_temp": 220,
    "bed_temp": 60
  }'
```

### 2. Print and Inspect

Print the generated calibration G-code and inspect results:

**Pressure Advance:**
- Look for sharp corners without bulging or gaps
- Best section = optimal PA value

**Flow Calibration:**
- Measure wall thickness with calipers
- Should match expected (typically 0.4mm for 0.4mm nozzle)
- Adjust flow_multiplier and re-test if needed

**Temperature Tower:**
- Inspect layer adhesion, stringing, surface finish
- Best section = optimal temperature

### 3. Save Calibration Results

After identifying optimal values:

```bash
curl -X POST http://localhost:8080/calibration/save \
  -H "Content-Type: application/json" \
  -d '{
    "printer_id": "ender3_01",
    "filament_name": "esun_pla_red",
    "material_type": "PLA",
    "brand": "Esun",
    "color": "Red",
    "pressure_advance": 0.055,
    "optimal_nozzle_temp": 205,
    "optimal_bed_temp": 60,
    "flow_multiplier": 0.98,
    "retraction_distance": 5.0,
    "retraction_speed": 45.0,
    "notes": "Slightly lower flow, good at 205C"
  }'
```

### 4. Use Calibrated Profiles

When slicing, the service will use the calibrated filament profile if available.

## Printer.cfg Integration

If you provide a path to your Klipper `printer.cfg`, the calibration generator will:
- Extract build volume limits
- Read current pressure advance settings
- Detect printer capabilities (input shaper, probe, etc.)
- Generate appropriate test prints within your printer's limits

```bash
# With printer.cfg
curl -X POST http://localhost:8080/calibration/generate \
  -H "Content-Type: application/json" \
  -d '{
    "printer_id": "ender3_01",
    "calibration_type": "pressure_advance",
    "filament_name": "esun_pla_red",
    "material_type": "PLA",
    "printer_config_path": "/home/pi/printer_data/config/printer.cfg",
    "nozzle_temp": 200,
    "bed_temp": 60
  }'
```

## Filament Profile Management

### List All Filaments

```bash
curl http://localhost:8080/filaments/ender3_01
```

Response:
```json
{
  "filaments": [
    {
      "id": 1,
      "printer_id": "ender3_01",
      "filament_name": "esun_pla_red",
      "material_type": "PLA",
      "brand": "Esun",
      "color": "Red",
      "pressure_advance": 0.055,
      "optimal_nozzle_temp": 205.0,
      "optimal_bed_temp": 60.0,
      "flow_multiplier": 0.98,
      "calibrated": true,
      "calibration_date": "2026-01-12T12:00:00"
    }
  ]
}
```

### Get Specific Filament

```bash
curl http://localhost:8080/filaments/ender3_01/esun_pla_red
```

## Calibration Types

### Pressure Advance Test
- **What it tests:** PA value for sharp corners without artifacts
- **Parameters:** `start_pa`, `end_pa`, steps (default 10)
- **Duration:** ~15-30 minutes
- **Output:** Tower with sections at different PA values

### Flow Calibration Cube
- **What it tests:** Extrusion multiplier accuracy
- **Parameters:** `flow_multiplier` (start at 1.0)
- **Duration:** ~30 minutes
- **Output:** 20mm calibration cube
- **Measurement:** Use calipers on walls

### Temperature Tower
- **What it tests:** Optimal nozzle temperature
- **Parameters:** `start_temp`, `end_temp`, `temp_step` (default 5°C)
- **Duration:** ~45-60 minutes
- **Output:** Tower with sections at different temps

## Best Practices

1. **Calibrate new filaments** — Always calibrate before production prints
2. **One spool = one profile** — Variations can occur between spools
3. **Recalibrate periodically** — Filament can absorb moisture
4. **Document results** — Use the `notes` field for observations
5. **Start with temperature** — Get optimal temp first, then flow, then PA

## Naming Convention

Use descriptive filament names:
- `esun_pla_red`
- `prusament_petg_galaxy_black`
- `overture_abs_white`
- `generic_pla_blue_spool2`

This helps track which physical spool is which.

## Integration with Slicing

When you slice with a calibrated filament:

```bash
curl -X POST http://localhost:8080/slice \
  -H "Content-Type: application/json" \
  -d '{
    "stl_path": "/path/to/model.stl",
    "printer_id": "ender3_01",
    "filament_name": "esun_pla_red",
    "profile": "standard"
  }'
```

The service will automatically use the calibrated values from that filament profile.

## Advanced: Klipper Integration

The generated calibration prints include Klipper-specific commands:

```gcode
SET_PRESSURE_ADVANCE ADVANCE=0.055
M221 S98  ; Set flow to 98%
```

After calibration, you can:
1. Update your `printer.cfg` with the optimal PA value
2. Use `SET_PRESSURE_ADVANCE` in your start G-code
3. Let the slicer service manage per-filament PA values

## Example: Complete Calibration Session

```bash
# 1. Generate temp tower
curl -X POST http://localhost:8080/calibration/generate \
  -d '{"printer_id":"ender3_01","calibration_type":"temperature","filament_name":"new_pla","material_type":"PLA","start_temp":190,"end_temp":220}' \
  -H "Content-Type: application/json"

# 2. Print, find optimal temp = 205°C

# 3. Generate flow cube at 205°C
curl -X POST http://localhost:8080/calibration/generate \
  -d '{"printer_id":"ender3_01","calibration_type":"flow","filament_name":"new_pla","material_type":"PLA","nozzle_temp":205}' \
  -H "Content-Type: application/json"

# 4. Print, measure, adjust flow = 0.97

# 5. Generate PA test at 205°C
curl -X POST http://localhost:8080/calibration/generate \
  -d '{"printer_id":"ender3_01","calibration_type":"pressure_advance","filament_name":"new_pla","material_type":"PLA","nozzle_temp":205}' \
  -H "Content-Type: application/json"

# 6. Print, find optimal PA = 0.048

# 7. Save complete profile
curl -X POST http://localhost:8080/calibration/save \
  -d '{"printer_id":"ender3_01","filament_name":"new_pla","material_type":"PLA","pressure_advance":0.048,"optimal_nozzle_temp":205,"optimal_bed_temp":60,"flow_multiplier":0.97}' \
  -H "Content-Type: application/json"

# 8. Done! Use "new_pla" in future slices
```

## Future Enhancements

- [ ] Auto-analysis of calibration prints (camera integration)
- [ ] Cloud sync of filament profiles
- [ ] Community filament database
- [ ] Multi-material profiles for MMU
- [ ] Input shaper calibration integration
