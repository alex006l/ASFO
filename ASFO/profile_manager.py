"""Profile management and mutation logic."""
from typing import Optional, List
from sqlmodel import Session, select
from datetime import datetime
from .models import PrintProfile, PrintFeedback


class ProfileManager:
    """Manage slicing profiles and mutations."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def get_or_create_profile(
        self,
        printer_id: str,
        material: str,
        nozzle_size: float,
        profile_name: str = "standard"
    ) -> PrintProfile:
        """Get latest profile version or create default."""
        # Find latest version
        statement = (
            select(PrintProfile)
            .where(PrintProfile.printer_id == printer_id)
            .where(PrintProfile.material == material)
            .where(PrintProfile.profile_name == profile_name)
            .where(PrintProfile.nozzle_size == nozzle_size)
            .order_by(PrintProfile.version.desc())
        )
        
        profile = self.session.exec(statement).first()
        
        if profile:
            return profile
        
        # Create default profile
        default = self._create_default_profile(
            printer_id, material, nozzle_size, profile_name
        )
        self.session.add(default)
        self.session.commit()
        self.session.refresh(default)
        return default
    
    def _create_default_profile(
        self,
        printer_id: str,
        material: str,
        nozzle_size: float,
        profile_name: str
    ) -> PrintProfile:
        """Create default profile based on material."""
        # Base defaults
        defaults = {
            "printer_id": printer_id,
            "material": material,
            "nozzle_size": nozzle_size,
            "profile_name": profile_name,
            "version": 1,
            "layer_height": 0.2,
            "wall_thickness": 0.8,
            "top_bottom_thickness": 0.8,
            "infill_density": 20.0,
            "print_speed": 50.0,
            "travel_speed": 150.0,
            "retraction_distance": 5.0,
            "retraction_speed": 45.0,
            "extrusion_multiplier": 1.0,
            "first_layer_speed": 20.0,
            "first_layer_height": 0.2,
            "created_at": datetime.utcnow(),  # Fix SQLModel default_factory issue
        }
        
        # Material-specific overrides
        if material.upper() == "PLA":
            defaults.update({
                "nozzle_temp": 200.0,
                "bed_temp": 60.0,
            })
        elif material.upper() == "PETG":
            defaults.update({
                "nozzle_temp": 230.0,
                "bed_temp": 80.0,
                "retraction_distance": 4.0,
            })
        elif material.upper() == "ABS":
            defaults.update({
                "nozzle_temp": 240.0,
                "bed_temp": 100.0,
                "print_speed": 40.0,
            })
        else:
            # Generic defaults
            defaults.update({
                "nozzle_temp": 200.0,
                "bed_temp": 60.0,
            })
        
        return PrintProfile(**defaults)
    
    def mutate_profile_from_feedback(
        self,
        feedback: PrintFeedback
    ) -> Optional[PrintProfile]:
        """
        Create new profile version based on feedback.
        
        Rules (small, bounded, reversible):
        - Under-extrusion: +2% flow OR +5°C
        - Over-extrusion: -2% flow OR -5°C
        - Stringing: +0.2mm retraction, -5°C
        - Adhesion: +5°C bed, -10% first layer speed
        - Warping: +5°C bed
        """
        if feedback.result == "success":
            # No mutation needed for success
            return None
        
        # Get current profile
        statement = (
            select(PrintProfile)
            .where(PrintProfile.printer_id == feedback.printer_id)
            .where(PrintProfile.material == feedback.material)
            .where(PrintProfile.profile_name == feedback.profile_name)
            .where(PrintProfile.version == feedback.profile_version)
        )
        current = self.session.exec(statement).first()
        
        if not current:
            return None
        
        # Clone and mutate
        new_profile = PrintProfile(
            printer_id=current.printer_id,
            material=current.material,
            nozzle_size=current.nozzle_size,
            profile_name=current.profile_name,
            version=current.version + 1,
            layer_height=current.layer_height,
            wall_thickness=current.wall_thickness,
            top_bottom_thickness=current.top_bottom_thickness,
            infill_density=current.infill_density,
            print_speed=current.print_speed,
            travel_speed=current.travel_speed,
            nozzle_temp=current.nozzle_temp,
            bed_temp=current.bed_temp,
            retraction_distance=current.retraction_distance,
            retraction_speed=current.retraction_speed,
            extrusion_multiplier=current.extrusion_multiplier,
            first_layer_speed=current.first_layer_speed,
            first_layer_height=current.first_layer_height,
            parent_version=current.version,
            mutation_reason=feedback.failure_type or "unknown"
        )
        
        # Apply mutation rules
        if feedback.failure_type == "under_extrusion":
            new_profile.extrusion_multiplier = min(1.2, new_profile.extrusion_multiplier + 0.02)
            new_profile.mutation_reason = "under_extrusion: +2% flow"
        
        elif feedback.failure_type == "over_extrusion":
            new_profile.extrusion_multiplier = max(0.8, new_profile.extrusion_multiplier - 0.02)
            new_profile.mutation_reason = "over_extrusion: -2% flow"
        
        elif feedback.failure_type == "stringing":
            new_profile.retraction_distance = min(8.0, new_profile.retraction_distance + 0.2)
            new_profile.nozzle_temp = max(180.0, new_profile.nozzle_temp - 5.0)
            new_profile.mutation_reason = "stringing: +0.2mm retract, -5°C"
        
        elif feedback.failure_type == "adhesion":
            new_profile.bed_temp = min(120.0, new_profile.bed_temp + 5.0)
            new_profile.first_layer_speed = max(10.0, new_profile.first_layer_speed * 0.9)
            new_profile.mutation_reason = "adhesion: +5°C bed, -10% first layer speed"
        
        elif feedback.failure_type == "warping":
            new_profile.bed_temp = min(120.0, new_profile.bed_temp + 5.0)
            new_profile.mutation_reason = "warping: +5°C bed"
        
        else:
            # No specific rule, don't mutate
            return None
        
        self.session.add(new_profile)
        self.session.commit()
        self.session.refresh(new_profile)
        return new_profile
