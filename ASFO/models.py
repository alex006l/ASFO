"""Data models for slicer service."""
from typing import Optional, Literal
from datetime import datetime
from pydantic import BaseModel, Field
from sqlmodel import SQLModel, Field as SQLField


# API Request/Response models
class SliceRequest(BaseModel):
    """Request to slice an STL file."""
    stl_path: str = Field(..., description="Path to STL file or upload via multipart")
    printer_id: str = Field(..., description="Printer identifier (e.g., 'ender3_01')")
    material: str = Field(default="PLA", description="Material type")
    profile: str = Field(default="standard", description="Profile name")
    nozzle_size: float = Field(default=0.4, description="Nozzle diameter in mm")


class SliceResponse(BaseModel):
    """Response from slicing operation."""
    gcode_path: str
    estimated_time_seconds: int
    used_profile: str
    profile_version: int
    filament_length_mm: Optional[float] = None
    filament_weight_g: Optional[float] = None


class UploadToMoonrakerRequest(BaseModel):
    """Request to upload G-code to Moonraker."""
    gcode_path: str
    printer_id: Optional[str] = None
    moonraker_url: Optional[str] = None
    start_print: bool = False
    filename: Optional[str] = None


class UploadToMoonrakerResponse(BaseModel):
    """Response from Moonraker upload."""
    success: bool
    moonraker_path: str
    message: Optional[str] = None


class FeedbackRequest(BaseModel):
    """Feedback after a print job."""
    printer_id: str
    material: str
    profile: str
    profile_version: int
    result: Literal["success", "failure"]
    failure_type: Optional[Literal[
        "under_extrusion",
        "over_extrusion",
        "stringing",
        "adhesion",
        "warping",
        "layer_shift",
        "blobs",
        "other"
    ]] = None
    quality_rating: Optional[int] = Field(None, ge=1, le=5)
    notes: Optional[str] = None


class FeedbackResponse(BaseModel):
    """Response after storing feedback."""
    feedback_id: int
    profile_updated: bool
    new_profile_version: Optional[int] = None


# Calibration models
class GenerateCalibrationRequest(BaseModel):
    """Request to generate calibration print."""
    printer_id: str
    calibration_type: Literal["pressure_advance", "flow", "temperature"]
    filament_name: str
    material_type: str = "PLA"
    
    # Printer config path (optional, for parsing capabilities)
    printer_config_path: Optional[str] = None
    
    # Calibration parameters
    nozzle_temp: float = 200.0
    bed_temp: float = 60.0
    
    # Type-specific parameters
    start_pa: Optional[float] = 0.0  # For pressure_advance
    end_pa: Optional[float] = 0.1
    start_temp: Optional[float] = 190.0  # For temperature
    end_temp: Optional[float] = 220.0
    flow_multiplier: Optional[float] = 1.0  # For flow


class GenerateCalibrationResponse(BaseModel):
    """Response from calibration print generation."""
    gcode_path: str
    calibration_type: str
    filament_name: str
    instructions: str


class SaveFilamentCalibrationRequest(BaseModel):
    """Save calibration results for a filament."""
    printer_id: str
    filament_name: str
    material_type: str
    brand: Optional[str] = None
    color: Optional[str] = None
    
    # Calibrated values
    pressure_advance: Optional[float] = None
    optimal_nozzle_temp: Optional[float] = None
    optimal_bed_temp: Optional[float] = None
    flow_multiplier: Optional[float] = None
    retraction_distance: Optional[float] = None
    retraction_speed: Optional[float] = None
    
    notes: Optional[str] = None


class SaveFilamentCalibrationResponse(BaseModel):
    """Response from saving filament calibration."""
    filament_profile_id: int
    filament_name: str
    message: str


# Database models
class FilamentProfile(SQLModel, table=True):
    """Filament-specific profiles (brand, color, etc)."""
    __tablename__ = "filament_profiles"
    
    id: Optional[int] = SQLField(default=None, primary_key=True)
    printer_id: str = SQLField(index=True)
    
    # Filament identification
    material_type: str = SQLField(index=True)  # PLA, PETG, ABS, etc.
    brand: Optional[str] = None
    color: Optional[str] = None
    filament_name: str = SQLField(index=True)  # Unique name (e.g., "esun_pla_red")
    
    # Klipper-specific parameters
    pressure_advance: Optional[float] = None
    pressure_advance_smooth_time: Optional[float] = 0.04
    
    # Temperature ranges (calibrated)
    optimal_nozzle_temp: float = 200.0
    optimal_bed_temp: float = 60.0
    
    # Flow calibration
    flow_multiplier: float = 1.0  # Extrusion multiplier
    
    # Other calibrated values
    retraction_distance: float = 5.0
    retraction_speed: float = 45.0
    
    # Metadata
    calibrated: bool = False
    calibration_date: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime = SQLField(default_factory=datetime.utcnow)


class PrintProfile(SQLModel, table=True):
    """Slicing profile versioning (linked to filament profile)."""
    __tablename__ = "print_profiles"
    
    id: Optional[int] = SQLField(default=None, primary_key=True)
    printer_id: str = SQLField(index=True)
    material: str = SQLField(index=True)
    nozzle_size: float
    profile_name: str
    version: int
    
    # Link to filament profile (optional)
    filament_profile_id: Optional[int] = None
    
    # Core slicing parameters (CuraEngine)
    layer_height: float = 0.2
    wall_thickness: float = 0.8
    top_bottom_thickness: float = 0.8
    infill_density: float = 20.0
    print_speed: float = 50.0
    travel_speed: float = 150.0
    
    # Temperature
    nozzle_temp: float = 200.0
    bed_temp: float = 60.0
    
    # Retraction
    retraction_distance: float = 5.0
    retraction_speed: float = 45.0
    
    # Extrusion
    extrusion_multiplier: float = 1.0
    
    # First layer
    first_layer_speed: float = 20.0
    first_layer_height: float = 0.2
    
    created_at: datetime = SQLField(default_factory=datetime.utcnow)
    parent_version: Optional[int] = None
    mutation_reason: Optional[str] = None


class PrintFeedback(SQLModel, table=True):
    """Feedback records from users."""
    __tablename__ = "print_feedback"
    
    id: Optional[int] = SQLField(default=None, primary_key=True)
    printer_id: str = SQLField(index=True)
    material: str = SQLField(index=True)
    profile_name: str
    profile_version: int
    
    result: str  # success/failure
    failure_type: Optional[str] = None
    quality_rating: Optional[int] = None
    notes: Optional[str] = None
    
    created_at: datetime = SQLField(default_factory=datetime.utcnow)


class PendingFeedback(SQLModel, table=True):
    """Pending feedback requests for completed prints."""
    __tablename__ = "pending_feedback"
    
    id: Optional[int] = SQLField(default=None, primary_key=True)
    filename: str = SQLField(index=True)
    printer_id: Optional[str] = None
    started_at: datetime
    completed_at: datetime
    state: str  # complete, cancelled, error
    dismissed: bool = False
    feedback_submitted: bool = False
    
    created_at: datetime = SQLField(default_factory=datetime.utcnow)
