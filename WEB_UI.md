# ASFO Web UI

## Access the Interface

Open your browser and navigate to:
- **Web UI**: `http://YOUR_PI_IP:8080/ui/`
- **API Docs**: `http://YOUR_PI_IP:8080/docs`

Replace `YOUR_PI_IP` with your Raspberry Pi's IP address (e.g., `192.168.1.19`).

## Features

### 🎯 Dashboard
- Real-time status monitoring
- Version information
- Job statistics (total jobs, queued jobs)

### 📤 File Upload
- Drag-and-drop STL file upload
- Automatic slicing after upload
- Progress feedback

### 📋 Job Management
- View all slicing jobs
- Monitor job status (pending, processing, completed, failed)
- Download generated G-code files

## Integration with Mainsail

### Option 1: Direct Access
1. Bookmark `http://YOUR_PI_IP:8080/ui/` in your browser
2. Access it alongside your Mainsail tab

### Option 2: Browser Extension (Recommended)
Install a browser extension like "Tab Manager Plus" to create a custom tab group:
- Mainsail (http://YOUR_PI_IP)
- ASFO Slicer (http://YOUR_PI_IP:8080/ui/)

### Option 3: Mainsail Mobile/Tablet View
On mobile devices:
1. Add both URLs to your home screen as web apps
2. Switch between them easily

## Usage Workflow

1. **Upload STL File**
   - Go to http://YOUR_PI_IP:8080/ui/
   - Drop your .stl file in the upload area
   - Click "Upload & Slice"

2. **Monitor Progress**
   - Job appears in "Recent Jobs" section
   - Status updates automatically every 5 seconds

3. **Download G-code**
   - Once status shows "completed"
   - Click "Download G-code" link
   - Load in your 3D printer

4. **Print from Mainsail**
   - Download G-code from ASFO UI
   - Upload to Mainsail G-code Files
   - Start print as usual

## API Integration

The Web UI uses the ASFO REST API:
- `GET /version` - Version info
- `GET /jobs` - List all jobs
- `POST /upload/stl` - Upload and slice STL file
- `GET /download/gcode/{job_id}` - Download G-code

See full API documentation at `http://YOUR_PI_IP:8080/docs`

## Troubleshooting

### UI Not Loading
```bash
# Check if service is running
sudo systemctl status ASFO

# Check logs
sudo journalctl -u ASFO -f

# Restart service
sudo systemctl restart ASFO
```

### Can't Access from Browser
```bash
# Verify port 8080 is open
curl http://localhost:8080/ui/

# Check firewall (if enabled)
sudo ufw status
sudo ufw allow 8080/tcp
```

### Jobs Not Appearing
```bash
# Check database
ls -la /var/lib/ASFO/

# Check API directly
curl http://localhost:8080/jobs
```

## Future Enhancements

Planned features:
- [ ] Native Mainsail navigation integration
- [ ] Real-time slicing progress
- [ ] Profile management UI
- [ ] Print feedback integration
- [ ] Batch upload support
- [ ] STL preview
- [ ] Custom slicer settings per job

## Development

To modify the UI:
1. Edit `/opt/ASFO/ASFO/static/index.html`
2. Restart ASFO: `sudo systemctl restart ASFO`
3. Refresh browser (Ctrl+F5 to clear cache)

The UI is a single-page application built with vanilla JavaScript - no build step required!
