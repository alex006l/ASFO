# Klipper Integration Guide

This document describes how ASFO integrates with Klipper firmware and the recommended settings.

## Features

### 1. Automatic Klipper Post-Processing

ASFO automatically applies Klipper-specific enhancements to all G-code:

- **Layer Tracking**: Adds `SET_PRINT_STATS_INFO` macros for real-time layer progress
- **Timelapse Support**: Adds `TIMELAPSE_TAKE_FRAME` for moonraker-timelapse
- **Moonraker Metadata**: Includes extra metadata comments for better file information

### 2. Optimized Default Settings

All profiles use Klipper-optimized defaults:

#### Speed Settings
- **Print Speed**: 60 mm/s (increased from generic 50 mm/s)
- **Travel Speed**: 200 mm/s (increased from generic 150 mm/s)
- **Jerk**: Disabled (Klipper uses `square_corner_velocity` instead)

#### Acceleration
Klipper handles acceleration dynamically, so fixed acceleration limits are not set in profiles.

### 3. Transparent Thumbnails

G-code includes embedded thumbnails with:
- Sizes: 32x32 and 300x300 pixels
- Format: PNG with transparent background
- Colors: Orange/coral (#FF6B35) with dark edges
- Compatible with Mainsail and Fluidd

## Recommended Klipper Configuration

### In printer.cfg

Ensure these macros are defined for full functionality:

```cfg
[gcode_macro SET_PRINT_STATS_INFO]
description: Set print statistics info
variable_total_layer: 0
variable_current_layer: 0
gcode:
    {% if params.TOTAL_LAYER %}
        SET_GCODE_VARIABLE MACRO=SET_PRINT_STATS_INFO VARIABLE=total_layer VALUE={params.TOTAL_LAYER|int}
    {% endif %}
    {% if params.CURRENT_LAYER %}
        SET_GCODE_VARIABLE MACRO=SET_PRINT_STATS_INFO VARIABLE=current_layer VALUE={params.CURRENT_LAYER|int}
    {% endif %}

[gcode_macro TIMELAPSE_TAKE_FRAME]
description: Take a timelapse frame (requires moonraker-timelapse)
gcode:
    # This will be handled by moonraker-timelapse if installed
    # If not installed, this macro does nothing
```

### In moonraker.conf

For automatic updates of ASFO (optional):

```cfg
[update_manager ASFO]
type: git_repo
path: /opt/ASFO
origin: https://github.com/alex006l/ASFO.git
primary_branch: main
managed_services: ASFO
```

## Klipper vs Generic Firmware Differences

| Setting | Generic | Klipper | Reason |
|---------|---------|---------|--------|
| Jerk Control | Enabled | Disabled | Klipper uses square_corner_velocity |
| Travel Speed | 150 mm/s | 200 mm/s | Klipper handles this better |
| Print Speed | 50 mm/s | 60 mm/s | Klipper's smoother motion allows faster printing |
| Acceleration | Fixed | Dynamic | Klipper adjusts based on printer.cfg |

## Material-Specific Optimizations

### PLA (Klipper-optimized)
- Nozzle: 200°C
- Bed: 60°C
- Print Speed: 60 mm/s
- Travel: 200 mm/s

### PETG (Klipper-optimized)
- Nozzle: 230°C
- Bed: 80°C
- Print Speed: 60 mm/s
- Retraction: 4.0 mm (reduced for PETG stringing)

### ABS (Klipper-optimized)
- Nozzle: 240°C
- Bed: 100°C
- Print Speed: 50 mm/s (slower for better layer adhesion)
- Travel: 200 mm/s

## Advanced Features

### Layer Progress Display

With `SET_PRINT_STATS_INFO`, Klipper/Mainsail will show:
- Current layer: X/Y
- Percentage complete based on layers
- More accurate time estimates

### Timelapse Videos

With moonraker-timelapse installed:
1. ASFO automatically adds `TIMELAPSE_TAKE_FRAME` at each layer change
2. Moonraker captures frames during printing
3. After print completes, Moonraker assembles the timelapse video

### Object Cancellation (Future)

The Klipper preprocessor supports object cancellation metadata, but this requires:
1. `preprocess_cancellation` binary (external tool)
2. Klipper configured with `[exclude_object]`

This feature is planned for future ASFO releases.

## Troubleshooting

### "Unknown Command: SET_PRINT_STATS_INFO"

Add the macro to your printer.cfg (see above).

### "Unknown Command: TIMELAPSE_TAKE_FRAME"

Either:
1. Install moonraker-timelapse, OR
2. Add an empty macro to printer.cfg (see above)

### Thumbnails Not Showing in Mainsail

Check:
1. Mainsail version (needs v2.0+)
2. G-code file has thumbnail headers ("; thumbnail begin")
3. File was sliced with ASFO v1.1+

## References

- [Klipper Documentation](https://www.klipper3d.org/)
- [Klipper Slicer Settings](https://www.klipper3d.org/Slicers.html)
- [moonraker-timelapse](https://github.com/mainsail-crew/moonraker-timelapse)
- [Klipper Preprocessor](https://github.com/pedrolamas/klipper-preprocessor)
