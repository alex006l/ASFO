"""Main FastAPI application."""
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
from sqlmodel import Session
from pathlib import Path
import uuid

from .database import init_db, get_session
from .models import (
    SliceRequest, SliceResponse,
    UploadToMoonrakerRequest, UploadToMoonrakerResponse,
    FeedbackRequest, FeedbackResponse,
    PrintFeedback,
    GenerateCalibrationRequest, GenerateCalibrationResponse,
    SaveFilamentCalibrationRequest, SaveFilamentCalibrationResponse,
    FilamentProfile
)
from .cura_engine import CuraEngineWrapper
from .moonraker_client import MoonrakerClient
from .profile_manager import ProfileManager
from .printer_config import PrinterConfigParser
from .calibration import CalibrationPrintGenerator
from .config import STL_TEMP_DIR, DEFAULT_MOONRAKER_URL
from .version import get_version_info, check_for_updates

app = FastAPI(
    title="Slicer Service",
    description="CuraEngine slicing service with feedback-driven profile optimization",
    version="0.1.0"
)

# Initialize DB on startup
@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/")
def root():
    """Health check and version info."""
    version_info = get_version_info()
    return {
        "status": "ok",
        "service": "ASFO",
        "version": version_info.get("version"),
        "commit": version_info.get("commit"),
        "branch": version_info.get("branch")
    }


@app.get("/version")
def get_version():
    """Get detailed version information."""
    return get_version_info()


@app.get("/check-updates")
def check_updates():
    """Check if updates are available (requires git fetch)."""
    update_info = check_for_updates()
    if update_info is None:
        return {"error": "Unable to check for updates", "available": False}
    return update_info


@app.post("/slice", response_model=SliceResponse)
def slice_model(
    request: SliceRequest,
    session: Session = Depends(get_session)
):
    """
    Slice an STL file using CuraEngine.
    
    - Retrieves or creates a profile for the printer/material combo
    - Invokes CuraEngine
    - Returns G-code path and metadata
    """
    # Get or create profile
    profile_mgr = ProfileManager(session)
    profile = profile_mgr.get_or_create_profile(
        printer_id=request.printer_id,
        material=request.material,
        nozzle_size=request.nozzle_size,
        profile_name=request.profile
    )
    
    # Slice
    engine = CuraEngineWrapper()
    output_name = f"{Path(request.stl_path).stem}_{request.material}_{profile.version}"
    
    try:
        result = engine.slice(
            stl_path=request.stl_path,
            profile=profile,
            output_name=output_name
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Slicing failed: {str(e)}")
    
    return SliceResponse(
        gcode_path=result["gcode_path"],
        estimated_time_seconds=result["estimated_time_seconds"],
        used_profile=profile.profile_name,
        profile_version=profile.version,
        filament_length_mm=result.get("filament_length_mm"),
        filament_weight_g=result.get("filament_weight_g")
    )


@app.post("/upload-stl")
async def upload_stl(file: UploadFile = File(...)):
    """
    Upload STL file for slicing.
    
    Returns a temporary path that can be used in /slice endpoint.
    """
    if not file.filename.lower().endswith(".stl"):
        raise HTTPException(status_code=400, detail="Only STL files allowed")
    
    # Save to temp directory
    file_id = str(uuid.uuid4())
    temp_path = STL_TEMP_DIR / f"{file_id}_{file.filename}"
    
    with open(temp_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    return {"stl_path": str(temp_path), "filename": file.filename}


@app.post("/upload-to-moonraker", response_model=UploadToMoonrakerResponse)
async def upload_to_moonraker(request: UploadToMoonrakerRequest):
    """
    Upload G-code to Moonraker and optionally start print.
    """
    moonraker_url = request.moonraker_url or DEFAULT_MOONRAKER_URL
    client = MoonrakerClient(moonraker_url)
    
    try:
        result = await client.upload_gcode(
            gcode_path=request.gcode_path,
            filename=request.filename,
            start_print=request.start_print
        )
        return UploadToMoonrakerResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@app.post("/feedback", response_model=FeedbackResponse)
def submit_feedback(
    request: FeedbackRequest,
    session: Session = Depends(get_session)
):
    """
    Submit feedback for a print job.
    
    - Stores feedback
    - Mutates profile if failure detected
    """
    # Store feedback
    feedback = PrintFeedback(
        printer_id=request.printer_id,
        material=request.material,
        profile_name=request.profile,
        profile_version=request.profile_version,
        result=request.result,
        failure_type=request.failure_type,
        quality_rating=request.quality_rating,
        notes=request.notes
    )
    session.add(feedback)
    session.commit()
    session.refresh(feedback)
    
    # Try to mutate profile
    profile_mgr = ProfileManager(session)
    new_profile = profile_mgr.mutate_profile_from_feedback(feedback)
    
    return FeedbackResponse(
        feedback_id=feedback.id,
        profile_updated=new_profile is not None,
        new_profile_version=new_profile.version if new_profile else None
    )


@app.get("/profiles/{printer_id}/{material}")
def get_profiles(
    printer_id: str,
    material: str,
    session: Session = Depends(get_session)
):
    """Get all profile versions for a printer/material combo."""
    from sqlmodel import select
    from .models import PrintProfile
    
    statement = (
        select(PrintProfile)
        .where(PrintProfile.printer_id == printer_id)
        .where(PrintProfile.material == material)
        .order_by(PrintProfile.version.desc())
    )
    
    profiles = session.exec(statement).all()
    return {"profiles": profiles}


@app.get("/feedback/{printer_id}")
def get_feedback_history(
    printer_id: str,
    session: Session = Depends(get_session)
):
    """Get feedback history for a printer."""
    from sqlmodel import select
    
    statement = (
        select(PrintFeedback)
        .where(PrintFeedback.printer_id == printer_id)
        .order_by(PrintFeedback.created_at.desc())
        .limit(50)
    )
    
    feedback = session.exec(statement).all()
    return {"feedback": feedback}


@app.post("/calibration/generate", response_model=GenerateCalibrationResponse)
def generate_calibration_print(
    request: GenerateCalibrationRequest,
    session: Session = Depends(get_session)
):
    """
    Generate a calibration test print for a specific filament.
    
    Supports:
    - pressure_advance: PA tower test
    - flow: Flow calibration cube
    - temperature: Temperature tower
    """
    # Parse printer config if provided
    if request.printer_config_path:
        parser = PrinterConfigParser(request.printer_config_path)
        caps = parser.parse()
    else:
        # Use defaults
        from .printer_config import PrinterCapabilities
        caps = PrinterCapabilities()
    
    generator = CalibrationPrintGenerator(caps)
    
    # Generate appropriate calibration print
    if request.calibration_type == "pressure_advance":
        gcode = generator.generate_pressure_advance_test(
            start_pa=request.start_pa or 0.0,
            end_pa=request.end_pa or 0.1,
            nozzle_temp=request.nozzle_temp,
            bed_temp=request.bed_temp
        )
        instructions = (
            "Print this tower and inspect the quality at each section. "
            "The best PA value is where corners are sharp without bulging or gaps. "
            "Use the value from the best-looking section."
        )
    
    elif request.calibration_type == "flow":
        gcode = generator.generate_flow_calibration_cube(
            nozzle_temp=request.nozzle_temp,
            bed_temp=request.bed_temp,
            flow_multiplier=request.flow_multiplier or 1.0
        )
        instructions = (
            "Measure the walls with calipers. They should be exactly 0.4mm (or 2x nozzle size). "
            "If thicker, reduce flow. If thinner, increase flow. "
            "Repeat with adjusted flow_multiplier until accurate."
        )
    
    elif request.calibration_type == "temperature":
        gcode = generator.generate_temperature_tower(
            start_temp=request.start_temp or 190.0,
            end_temp=request.end_temp or 220.0,
            bed_temp=request.bed_temp
        )
        instructions = (
            "Inspect each section of the tower. "
            "Look for the best layer adhesion, minimal stringing, and good surface finish. "
            "Use the temperature from the best section."
        )
    
    else:
        raise HTTPException(status_code=400, detail="Invalid calibration_type")
    
    # Save G-code
    filename = f"{request.printer_id}_{request.filament_name}_{request.calibration_type}"
    gcode_path = generator.save_calibration_print(gcode, filename)
    
    return GenerateCalibrationResponse(
        gcode_path=gcode_path,
        calibration_type=request.calibration_type,
        filament_name=request.filament_name,
        instructions=instructions
    )


@app.post("/calibration/save", response_model=SaveFilamentCalibrationResponse)
def save_filament_calibration(
    request: SaveFilamentCalibrationRequest,
    session: Session = Depends(get_session)
):
    """
    Save calibration results for a specific filament.
    
    Creates or updates a filament profile with calibrated values.
    """
    from sqlmodel import select
    from datetime import datetime
    
    # Check if filament profile exists
    statement = (
        select(FilamentProfile)
        .where(FilamentProfile.printer_id == request.printer_id)
        .where(FilamentProfile.filament_name == request.filament_name)
    )
    
    filament = session.exec(statement).first()
    
    if filament:
        # Update existing
        if request.pressure_advance is not None:
            filament.pressure_advance = request.pressure_advance
        if request.optimal_nozzle_temp is not None:
            filament.optimal_nozzle_temp = request.optimal_nozzle_temp
        if request.optimal_bed_temp is not None:
            filament.optimal_bed_temp = request.optimal_bed_temp
        if request.flow_multiplier is not None:
            filament.flow_multiplier = request.flow_multiplier
        if request.retraction_distance is not None:
            filament.retraction_distance = request.retraction_distance
        if request.retraction_speed is not None:
            filament.retraction_speed = request.retraction_speed
        if request.notes:
            filament.notes = request.notes
        
        filament.calibrated = True
        filament.calibration_date = datetime.utcnow()
        
        message = f"Updated calibration for {request.filament_name}"
    
    else:
        # Create new
        filament = FilamentProfile(
            printer_id=request.printer_id,
            filament_name=request.filament_name,
            material_type=request.material_type,
            brand=request.brand,
            color=request.color,
            pressure_advance=request.pressure_advance or 0.0,
            optimal_nozzle_temp=request.optimal_nozzle_temp or 200.0,
            optimal_bed_temp=request.optimal_bed_temp or 60.0,
            flow_multiplier=request.flow_multiplier or 1.0,
            retraction_distance=request.retraction_distance or 5.0,
            retraction_speed=request.retraction_speed or 45.0,
            notes=request.notes,
            calibrated=True,
            calibration_date=datetime.utcnow()
        )
        session.add(filament)
        message = f"Created new calibration profile for {request.filament_name}"
    
    session.commit()
    session.refresh(filament)
    
    return SaveFilamentCalibrationResponse(
        filament_profile_id=filament.id,
        filament_name=filament.filament_name,
        message=message
    )


@app.get("/filaments/{printer_id}")
def get_filament_profiles(
    printer_id: str,
    session: Session = Depends(get_session)
):
    """Get all calibrated filament profiles for a printer."""
    from sqlmodel import select
    
    statement = (
        select(FilamentProfile)
        .where(FilamentProfile.printer_id == printer_id)
        .order_by(FilamentProfile.created_at.desc())
    )
    
    filaments = session.exec(statement).all()
    return {"filaments": filaments}


@app.get("/filaments/{printer_id}/{filament_name}")
def get_filament_profile(
    printer_id: str,
    filament_name: str,
    session: Session = Depends(get_session)
):
    """Get a specific filament profile."""
    from sqlmodel import select
    
    statement = (
        select(FilamentProfile)
        .where(FilamentProfile.printer_id == printer_id)
        .where(FilamentProfile.filament_name == filament_name)
    )
    
    filament = session.exec(statement).first()
    
    if not filament:
        raise HTTPException(status_code=404, detail="Filament profile not found")
    
    return filament
