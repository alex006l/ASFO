"""API endpoint for system info and version management."""
from pathlib import Path
from typing import Dict, Any, Optional
import subprocess
import os


def get_version_info() -> Dict[str, Any]:
    """Get current version info from git."""
    version_info = {
        "version": "1.1.0-3dviewer",
        "commit": None,
        "branch": None,
        "is_dirty": False,
        "update_available": None
    }
    
    try:
        # Get current commit hash
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=Path(__file__).parent.parent,
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            version_info["commit"] = result.stdout.strip()[:8]
        
        # Get current branch
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=Path(__file__).parent.parent,
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            version_info["branch"] = result.stdout.strip()
        
        # Check if working directory is dirty
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=Path(__file__).parent.parent,
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            version_info["is_dirty"] = bool(result.stdout.strip())
    
    except Exception:
        pass  # Git not available or not a git repo
    
    return version_info


def check_for_updates() -> Optional[Dict[str, Any]]:
    """Check if updates are available (requires git fetch)."""
    try:
        # Fetch latest
        subprocess.run(
            ["git", "fetch", "origin"],
            cwd=Path(__file__).parent.parent,
            capture_output=True,
            timeout=10
        )
        
        # Compare local with remote
        result = subprocess.run(
            ["git", "rev-list", "HEAD..origin/main", "--count"],
            cwd=Path(__file__).parent.parent,
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            commits_behind = int(result.stdout.strip())
            if commits_behind > 0:
                return {
                    "update_available": True,
                    "commits_behind": commits_behind,
                    "message": f"{commits_behind} update(s) available"
                }
        
        return {"update_available": False, "commits_behind": 0}
    
    except Exception:
        return None
