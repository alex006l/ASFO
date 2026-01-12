# Mainsail UI Extension Guide

## Overview
This guide shows how to integrate the slicing service into Mainsail **without forking** Mainsail initially.

## Architecture
```
┌──────────────────┐
│  Mainsail UI     │
│  (Vue.js SPA)    │
└────────┬─────────┘
         │
         ├─────────► Moonraker API (printer control, files)
         │
         └─────────► Slicer Service API (slicing, feedback)
                     http://localhost:8080
```

## Integration Approach (3 options)

### Option 1: Iframe Panel (Quickest)
Add a custom iframe panel to Mainsail that loads your slicing UI.

**Steps:**
1. Create a standalone HTML page (`slicer_ui.html`) that talks to your API
2. Host it on the same Pi (e.g., via nginx or the slicer service itself)
3. Add iframe to Mainsail:
   - Mainsail allows custom panels via config
   - Add to `moonraker.conf`:
     ```
     [update_manager slicer_panel]
     type: web
     repo: <your-repo>
     path: /path/to/slicer_ui
     ```

**Pros:** Zero Mainsail code changes, fast iteration
**Cons:** Iframe overhead, less native feel

### Option 2: Mainsail Plugin (Recommended)
Create a Mainsail-compatible Vue component as a plugin.

**Steps:**
1. Fork Mainsail (or submit PR later)
2. Add a new panel component in `src/components/panels/`
3. Register in sidebar navigation
4. Component makes HTTP calls to slicer service

**File structure:**
```
src/components/panels/SlicerPanel.vue
src/store/slicer/               # Vuex store for slicer state
```

**Sample component (SlicerPanel.vue):**
```vue
<template>
  <v-card>
    <v-card-title>Slice & Print</v-card-title>
    <v-card-text>
      <!-- STL Upload -->
      <v-file-input
        label="Upload STL"
        accept=".stl"
        @change="uploadStl"
      />
      
      <!-- Profile Selection -->
      <v-select
        v-model="selectedProfile"
        :items="['standard', 'fast', 'quality']"
        label="Profile"
      />
      
      <!-- Material -->
      <v-select
        v-model="material"
        :items="['PLA', 'PETG', 'ABS']"
        label="Material"
      />
      
      <!-- Slice Button -->
      <v-btn @click="sliceModel" color="primary">
        Slice
      </v-btn>
      
      <!-- Results -->
      <div v-if="sliceResult">
        <p>Estimated time: {{ sliceResult.estimated_time_seconds / 60 }} min</p>
        <v-btn @click="uploadAndPrint">Upload & Print</v-btn>
      </div>
    </v-card-text>
  </v-card>
</template>

<script>
export default {
  data() {
    return {
      stlPath: null,
      selectedProfile: 'standard',
      material: 'PLA',
      sliceResult: null,
      slicerServiceUrl: 'http://localhost:8080'
    }
  },
  methods: {
    async uploadStl(file) {
      const formData = new FormData()
      formData.append('file', file)
      
      const response = await fetch(`${this.slicerServiceUrl}/upload-stl`, {
        method: 'POST',
        body: formData
      })
      const data = await response.json()
      this.stlPath = data.stl_path
    },
    
    async sliceModel() {
      const response = await fetch(`${this.slicerServiceUrl}/slice`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          stl_path: this.stlPath,
          printer_id: 'ender3_01',  // Get from Mainsail config
          material: this.material,
          profile: this.selectedProfile,
          nozzle_size: 0.4
        })
      })
      this.sliceResult = await response.json()
    },
    
    async uploadAndPrint() {
      await fetch(`${this.slicerServiceUrl}/upload-to-moonraker`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          gcode_path: this.sliceResult.gcode_path,
          moonraker_url: window.location.origin,  // Use Mainsail's Moonraker
          start_print: true
        })
      })
      alert('Print started!')
    }
  }
}
</script>
```

### Option 3: Native Mainsail Extension (Future)
Wait for Mainsail's official plugin API (if/when released).

## Feedback Collection

### Post-Print Modal
Hook into Moonraker's `print_done` event to show a feedback modal.

**In Mainsail:**
```javascript
// Listen for print completion
this.$socket.on('notify_status_update', (data) => {
  if (data.print_stats?.state === 'complete') {
    this.showFeedbackModal()
  }
})

// Show modal
showFeedbackModal() {
  // Display Vue dialog with:
  // - Success/Failure radio
  // - Failure type dropdown (if failure)
  // - Quality slider (1-5)
  // - Notes textarea
  
  // On submit, POST to /feedback endpoint
}
```

**Feedback Form Fields:**
- Result: `success` / `failure`
- Failure type (if failure): under_extrusion, stringing, adhesion, etc.
- Quality rating: 1-5 stars
- Notes: free text

**Example submit:**
```javascript
async submitFeedback() {
  await fetch(`${slicerServiceUrl}/feedback`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      printer_id: this.printerId,
      material: this.lastPrintMaterial,
      profile: this.lastPrintProfile,
      profile_version: this.lastPrintProfileVersion,
      result: this.feedbackResult,
      failure_type: this.feedbackFailureType,
      quality_rating: this.qualityRating,
      notes: this.feedbackNotes
    })
  })
}
```

## Configuration

### Mainsail Config

Add to Mainsail's config (or custom config file):
```yaml
ASFO:
  enabled: true
  url: "http://localhost:8080"
  default_printer_id: "ender3_01"
  auto_feedback: true  # Auto-prompt after print
```

### Moonraker Update Manager

To enable updates from Mainsail's update menu, add this to your `moonraker.conf`:

```ini
[update_manager ASFO]
type: git_repo
path: /opt/ASFO
origin: https://github.com/alex006l/ASFO.git
managed_services: ASFO
primary_branch: main
virtualenv: /opt/ASFO/venv
requirements: requirements.txt
install_script: scripts/install_update.sh
```

Then restart Moonraker:
```bash
sudo systemctl restart moonraker
```

After this, the Slicer Service will appear in Mainsail's Machine > Update Manager tab, alongside Klipper, Moonraker, and Mainsail itself.

**Update process:**
1. Mainsail shows when updates are available
2. Click "Update" button
3. Moonraker pulls latest code from GitHub
4. Runs update script (installs new dependencies)
5. Restarts ASFO automatically
6. Done!

## Multi-Printer Support

For multi-printer setups, ensure each printer has a unique `printer_id`.

**In Mainsail config per printer:**
```yaml
printer_id: "ender3_01"
# or
printer_id: "prusa_mk3_02"
```

Pass this `printer_id` to all slicer service requests.

## Rollback Support

Moonraker's update manager supports rollback if an update causes issues:

1. Go to Mainsail > Machine > Update Manager
2. Find "ASFO" in the list
3. Click the dropdown next to Update
4. Select "Rollback to previous version"
5. Service will revert to the last working commit

## Security Notes
- Run slicer service on localhost or local network
- For remote access, use reverse proxy with authentication
- Consider API keys for production (already supported via env var)

## Testing
1. Start slicer service: `uvicorn ASFO.app:app --host 0.0.0.0 --port 8080`
2. Test with curl:
   ```bash
   # Upload STL
   curl -F "file=@benchy.stl" http://localhost:8080/upload-stl
   
   # Slice (use path from upload response)
   curl -X POST http://localhost:8080/slice \
     -H "Content-Type: application/json" \
     -d '{
       "stl_path": "/var/lib/ASFO/stl_temp/abc-benchy.stl",
       "printer_id": "ender3_01",
       "material": "PLA",
       "profile": "standard",
       "nozzle_size": 0.4
     }'
   ```

## Future Enhancements
- WebSocket support for real-time slicing progress
- Cloud profile sync across multiple printers
- Advanced analytics dashboard
- Integration with print farm management

## Next Steps
1. Implement Option 1 (iframe) for quick prototype
2. Test feedback loop with real prints
3. Refine mutation rules based on data
4. Consider Option 2 (plugin) for production
