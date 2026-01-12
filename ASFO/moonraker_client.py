"""Moonraker API client for G-code upload."""
import httpx
from pathlib import Path
from typing import Optional


class MoonrakerClient:
    """Client for Moonraker API operations."""
    
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
    
    async def upload_gcode(
        self,
        gcode_path: str,
        filename: Optional[str] = None,
        start_print: bool = False
    ) -> dict:
        """
        Upload G-code file to Moonraker.
        
        Uses POST /server/files/upload endpoint.
        """
        gcode_file = Path(gcode_path)
        if not gcode_file.exists():
            raise FileNotFoundError(f"G-code file not found: {gcode_path}")
        
        upload_filename = filename or gcode_file.name
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            with open(gcode_file, "rb") as f:
                files = {"file": (upload_filename, f, "application/octet-stream")}
                data = {"root": "gcodes"}
                
                response = await client.post(
                    f"{self.base_url}/server/files/upload",
                    files=files,
                    data=data
                )
                response.raise_for_status()
                result = response.json()
        
        moonraker_path = f"gcodes/{upload_filename}"
        
        # Optionally start print
        if start_print:
            await self.start_print(moonraker_path)
        
        return {
            "success": True,
            "moonraker_path": moonraker_path,
            "message": result.get("result", "Upload successful")
        }
    
    async def start_print(self, filename: str) -> dict:
        """Start print job on Moonraker."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{self.base_url}/printer/print/start",
                json={"filename": filename}
            )
            response.raise_for_status()
            return response.json()
