"""
Print completion monitoring and feedback collection.
Polls Moonraker for print status and triggers feedback requests.
"""
import asyncio
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from .moonraker_client import MoonrakerClient

logger = logging.getLogger("ASFO.print_monitor")


class PrintMonitor:
    """Monitor print jobs and collect completion status."""
    
    def __init__(self, moonraker_url: str):
        self.moonraker = MoonrakerClient(moonraker_url)
        self.active_prints: Dict[str, Dict[str, Any]] = {}
        self.monitoring = False
    
    async def start_monitoring(self):
        """Start monitoring print jobs."""
        self.monitoring = True
        logger.info("Print monitor started")
        
        while self.monitoring:
            try:
                await self._check_print_status()
                await asyncio.sleep(5)  # Check every 5 seconds
            except Exception as e:
                logger.error(f"Error in print monitor: {e}")
                await asyncio.sleep(10)  # Wait longer on error
    
    def stop_monitoring(self):
        """Stop monitoring."""
        self.monitoring = False
        logger.info("Print monitor stopped")
    
    async def _check_print_status(self):
        """Check current print status from Moonraker."""
        try:
            status = await self.moonraker.get_print_status()
            
            if not status:
                return
            
            state = status.get('state', 'unknown')
            filename = status.get('filename', '')
            
            # Track active prints
            if state == 'printing' and filename:
                if filename not in self.active_prints:
                    self.active_prints[filename] = {
                        'started_at': datetime.utcnow(),
                        'filename': filename,
                        'state': 'printing'
                    }
                    logger.info(f"Started tracking print: {filename}")
            
            # Detect print completion
            elif state in ['complete', 'cancelled', 'error'] and filename:
                if filename in self.active_prints:
                    print_info = self.active_prints[filename]
                    print_info['completed_at'] = datetime.utcnow()
                    print_info['final_state'] = state
                    
                    # Trigger feedback request
                    await self._trigger_feedback_request(print_info)
                    
                    # Remove from active tracking
                    del self.active_prints[filename]
                    logger.info(f"Print completed: {filename} - {state}")
        
        except Exception as e:
            logger.error(f"Error checking print status: {e}")
    
    async def _trigger_feedback_request(self, print_info: Dict[str, Any]):
        """Trigger feedback request for completed print."""
        # Store pending feedback request
        # This will be picked up by the UI
        feedback_data = {
            'filename': print_info['filename'],
            'started_at': print_info['started_at'].isoformat(),
            'completed_at': print_info['completed_at'].isoformat(),
            'state': print_info['final_state'],
            'success': print_info['final_state'] == 'complete'
        }
        
        # Store in a queue that UI can poll
        # For now, just log it
        logger.info(f"Feedback requested for: {feedback_data}")
        
        # TODO: Implement persistent storage for pending feedback requests
        # This could be stored in the database or a Redis queue


# Global monitor instance
_monitor: Optional[PrintMonitor] = None


def get_print_monitor(moonraker_url: str) -> PrintMonitor:
    """Get or create print monitor instance."""
    global _monitor
    if _monitor is None:
        _monitor = PrintMonitor(moonraker_url)
    return _monitor
