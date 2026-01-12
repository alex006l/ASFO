# ASFO Logging Feature

## Overview
Comprehensive logging system with file output and web-based log viewer for monitoring and debugging ASFO operations.

## Log Configuration

### Log File Location
- **Path**: `/var/lib/ASFO/logs/asfo.log`
- **Owner**: `asfo:asfo` (created by service)
- **Format**: `timestamp - logger - level - message`

### Log Levels
- **INFO**: Normal operations (startup, uploads, slicing)
- **WARNING**: Non-critical issues (rejected files)
- **ERROR**: Failures with stack traces
- **DEBUG**: Detailed diagnostics (health checks)

### Log Output
Logs are written to both:
1. **File**: `/var/lib/ASFO/logs/asfo.log` (persistent)
2. **Console**: `stdout` (visible in `journalctl -u ASFO`)

## Logged Events

### Startup
```
2026-01-12 11:38:23,409 - ASFO - INFO - Starting ASFO Slicer Service
2026-01-12 11:38:23,413 - ASFO - INFO - Version: 0.1.0 (commit: ae467f99)
2026-01-12 11:38:23,415 - ASFO - INFO - Database initialized
```

### File Upload
```
2026-01-12 11:40:15,234 - ASFO - INFO - Upload request: model.stl | Content-Type: application/octet-stream
2026-01-12 11:40:15,567 - ASFO - INFO - File uploaded successfully: /tmp/ASFO_stl/abc123_model.stl (2456789 bytes)
```

### Slicing Operations
```
2026-01-12 11:40:20,123 - ASFO - INFO - Slice request: /tmp/ASFO_stl/abc123_model.stl | Printer: ender3_01 | Material: PLA
2026-01-12 11:40:20,234 - ASFO - INFO - Using profile: standard v1
2026-01-12 11:40:20,345 - ASFO - INFO - Starting slicing: model_PLA_1
2026-01-12 11:40:45,678 - ASFO - INFO - Slicing complete: /var/lib/ASFO/gcode/model_PLA_1.gcode | Est. time: 3600s
```

### Errors
```
2026-01-12 11:41:00,123 - ASFO - ERROR - Slicing failed: CuraEngine returned non-zero exit code: 1
Traceback (most recent call last):
  ...
```

## Accessing Logs

### 1. Web UI (Easiest)
Visit: `http://YOUR_PI_IP:8080/ui/`

Scroll down to the **📜 Logs** section:
- Shows last 50 lines by default
- Click **🔄 Refresh** to update
- Auto-loads on page load

### 2. API Endpoint
```bash
# Get last 100 lines (default)
curl http://YOUR_PI_IP:8080/logs

# Get last 20 lines
curl http://YOUR_PI_IP:8080/logs?lines=20

# Get last 500 lines
curl http://YOUR_PI_IP:8080/logs?lines=500
```

### 3. Direct File Access (SSH)
```bash
# View entire log file
sudo cat /var/lib/ASFO/logs/asfo.log

# Follow logs in real-time
sudo tail -f /var/lib/ASFO/logs/asfo.log

# Last 50 lines
sudo tail -50 /var/lib/ASFO/logs/asfo.log

# Search for errors
sudo grep ERROR /var/lib/ASFO/logs/asfo.log

# Search for specific STL file
sudo grep "model.stl" /var/lib/ASFO/logs/asfo.log
```

### 4. Systemd Journal
```bash
# View service logs (console output)
sudo journalctl -u ASFO -f

# Last 100 lines
sudo journalctl -u ASFO -n 100

# Since boot
sudo journalctl -u ASFO -b

# Errors only
sudo journalctl -u ASFO -p err
```

## Log Rotation

To prevent logs from growing indefinitely, set up log rotation:

```bash
sudo nano /etc/logrotate.d/asfo
```

Add:
```
/var/lib/ASFO/logs/asfo.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0644 asfo asfo
}
```

This will:
- Rotate logs daily
- Keep 7 days of logs
- Compress old logs
- Create new log files with proper permissions

Test rotation:
```bash
sudo logrotate -f /etc/logrotate.d/asfo
```

## Troubleshooting

### Logs Not Appearing
```bash
# Check log directory exists
ls -la /var/lib/ASFO/logs/

# Check permissions
sudo chown -R asfo:asfo /var/lib/ASFO/logs/
sudo chmod 755 /var/lib/ASFO/logs/
sudo chmod 644 /var/lib/ASFO/logs/asfo.log

# Restart service
sudo systemctl restart ASFO
```

### Log File Too Large
```bash
# Check size
du -h /var/lib/ASFO/logs/asfo.log

# Truncate (keep last 1000 lines)
tail -1000 /var/lib/ASFO/logs/asfo.log | sudo tee /var/lib/ASFO/logs/asfo.log

# Or clear completely
sudo truncate -s 0 /var/lib/ASFO/logs/asfo.log
```

### Debug Mode
To enable more verbose logging, modify `/opt/ASFO/ASFO/app.py`:

```python
logging.basicConfig(
    level=logging.DEBUG,  # Changed from INFO
    ...
)
```

Then restart:
```bash
sudo systemctl restart ASFO
```

## Log Analysis

### Find All Slicing Operations
```bash
sudo grep "Slicing complete" /var/lib/ASFO/logs/asfo.log
```

### Count Uploads Today
```bash
sudo grep "$(date +%Y-%m-%d)" /var/lib/ASFO/logs/asfo.log | grep "Upload request" | wc -l
```

### Find Errors
```bash
sudo grep ERROR /var/lib/ASFO/logs/asfo.log | tail -10
```

### Average Slicing Time
```bash
sudo grep "Slicing complete" /var/lib/ASFO/logs/asfo.log | grep -oP 'Est\. time: \K\d+' | awk '{sum+=$1; count++} END {print sum/count}'
```

## Integration with Monitoring Tools

### Prometheus/Grafana
Create a log parser to extract metrics:
- Upload count
- Slice success rate
- Average slice time
- Error rate

### Alerting
Set up alerts for:
- Multiple consecutive errors
- Slicing taking too long (> threshold)
- Service restarts

### Log Aggregation
Forward logs to centralized systems:
- ELK Stack (Elasticsearch, Logstash, Kibana)
- Graylog
- Splunk
- Loki

Example with rsyslog:
```bash
sudo nano /etc/rsyslog.d/asfo.conf
```

Add:
```
$ModLoad imfile
$InputFileName /var/lib/ASFO/logs/asfo.log
$InputFileTag asfo:
$InputFileStateFile stat-asfo
$InputFileSeverity info
$InputRunFileMonitor
*.* @@your-log-server:514
```

## Best Practices

1. **Regular Monitoring**: Check logs daily for errors
2. **Log Rotation**: Prevent disk space issues
3. **Backup Logs**: Include in backup strategy
4. **Sensitive Data**: Logs don't contain credentials or user data
5. **Performance**: Logging has minimal performance impact
6. **Retention**: Keep at least 7 days for troubleshooting

## Future Enhancements

Planned improvements:
- [ ] Auto-refresh logs in web UI (WebSocket)
- [ ] Log filtering by level/module in UI
- [ ] Download logs from web UI
- [ ] Performance metrics dashboard
- [ ] Structured logging (JSON format)
- [ ] Log aggregation service integration
- [ ] Email alerts on errors
- [ ] Log search functionality in UI
