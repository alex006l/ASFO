"""Unit tests for slicer service."""
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine, SQLModel
from sqlmodel.pool import StaticPool

from ASFO.app import app
from ASFO.database import get_session
from ASFO.models import PrintProfile, PrintFeedback, FilamentProfile
from ASFO.profile_manager import ProfileManager


# Test database setup
@pytest.fixture(name="session")
def session_fixture():
    """Create test database session."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session):
    """Create test client with overridden session."""
    def get_session_override():
        return session
    
    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


# Tests
def test_root(client: TestClient):
    """Test health check endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_create_default_profile(session: Session):
    """Test default profile creation."""
    mgr = ProfileManager(session)
    profile = mgr.get_or_create_profile(
        printer_id="test_printer",
        material="PLA",
        nozzle_size=0.4,
        profile_name="standard"
    )
    
    assert profile.version == 1
    assert profile.nozzle_temp == 200.0
    assert profile.bed_temp == 60.0
    assert profile.extrusion_multiplier == 1.0


def test_profile_mutation_under_extrusion(session: Session):
    """Test profile mutation for under-extrusion."""
    # Create initial profile
    mgr = ProfileManager(session)
    profile = mgr.get_or_create_profile(
        printer_id="test_printer",
        material="PLA",
        nozzle_size=0.4,
        profile_name="standard"
    )
    
    # Submit failure feedback
    feedback = PrintFeedback(
        printer_id="test_printer",
        material="PLA",
        profile_name="standard",
        profile_version=1,
        result="failure",
        failure_type="under_extrusion"
    )
    session.add(feedback)
    session.commit()
    
    # Mutate profile
    new_profile = mgr.mutate_profile_from_feedback(feedback)
    
    assert new_profile is not None
    assert new_profile.version == 2
    assert new_profile.extrusion_multiplier > profile.extrusion_multiplier
    assert new_profile.parent_version == 1


def test_profile_mutation_stringing(session: Session):
    """Test profile mutation for stringing."""
    mgr = ProfileManager(session)
    profile = mgr.get_or_create_profile(
        printer_id="test_printer",
        material="PETG",
        nozzle_size=0.4,
        profile_name="standard"
    )
    
    feedback = PrintFeedback(
        printer_id="test_printer",
        material="PETG",
        profile_name="standard",
        profile_version=1,
        result="failure",
        failure_type="stringing"
    )
    session.add(feedback)
    session.commit()
    
    new_profile = mgr.mutate_profile_from_feedback(feedback)
    
    assert new_profile is not None
    assert new_profile.retraction_distance > profile.retraction_distance
    assert new_profile.nozzle_temp < profile.nozzle_temp


def test_profile_mutation_adhesion(session: Session):
    """Test profile mutation for adhesion issues."""
    mgr = ProfileManager(session)
    profile = mgr.get_or_create_profile(
        printer_id="test_printer",
        material="ABS",
        nozzle_size=0.4,
        profile_name="standard"
    )
    
    feedback = PrintFeedback(
        printer_id="test_printer",
        material="ABS",
        profile_name="standard",
        profile_version=1,
        result="failure",
        failure_type="adhesion"
    )
    session.add(feedback)
    session.commit()
    
    new_profile = mgr.mutate_profile_from_feedback(feedback)
    
    assert new_profile is not None
    assert new_profile.bed_temp > profile.bed_temp
    assert new_profile.first_layer_speed < profile.first_layer_speed


def test_no_mutation_on_success(session: Session):
    """Test that success feedback doesn't mutate profile."""
    mgr = ProfileManager(session)
    profile = mgr.get_or_create_profile(
        printer_id="test_printer",
        material="PLA",
        nozzle_size=0.4,
        profile_name="standard"
    )
    
    feedback = PrintFeedback(
        printer_id="test_printer",
        material="PLA",
        profile_name="standard",
        profile_version=1,
        result="success",
        quality_rating=5
    )
    session.add(feedback)
    session.commit()
    
    new_profile = mgr.mutate_profile_from_feedback(feedback)
    
    assert new_profile is None


def test_material_specific_defaults(session: Session):
    """Test material-specific default profiles."""
    mgr = ProfileManager(session)
    
    # PLA
    pla = mgr.get_or_create_profile("test", "PLA", 0.4)
    assert pla.nozzle_temp == 200.0
    assert pla.bed_temp == 60.0
    
    # PETG
    petg = mgr.get_or_create_profile("test", "PETG", 0.4)
    assert petg.nozzle_temp == 230.0
    assert petg.bed_temp == 80.0
    
    # ABS
    abs_profile = mgr.get_or_create_profile("test", "ABS", 0.4)
    assert abs_profile.nozzle_temp == 240.0
    assert abs_profile.bed_temp == 100.0


def test_feedback_endpoint(client: TestClient, session: Session):
    """Test feedback submission endpoint."""
    # Create profile first
    mgr = ProfileManager(session)
    mgr.get_or_create_profile("test_printer", "PLA", 0.4)
    
    response = client.post("/feedback", json={
        "printer_id": "test_printer",
        "material": "PLA",
        "profile": "standard",
        "profile_version": 1,
        "result": "failure",
        "failure_type": "under_extrusion",
        "quality_rating": 2,
        "notes": "Walls too thin"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["feedback_id"] > 0
    assert data["profile_updated"] is True
    assert data["new_profile_version"] == 2


def test_get_profiles_endpoint(client: TestClient, session: Session):
    """Test profile retrieval endpoint."""
    # Create a profile
    mgr = ProfileManager(session)
    mgr.get_or_create_profile("test_printer", "PLA", 0.4)
    
    response = client.get("/profiles/test_printer/PLA")
    assert response.status_code == 200
    data = response.json()
    assert len(data["profiles"]) == 1
    assert data["profiles"][0]["version"] == 1


def test_generate_calibration_print(client: TestClient):
    """Test calibration print generation."""
    response = client.post("/calibration/generate", json={
        "printer_id": "test_printer",
        "calibration_type": "pressure_advance",
        "filament_name": "test_pla",
        "material_type": "PLA",
        "nozzle_temp": 200,
        "bed_temp": 60,
        "start_pa": 0.0,
        "end_pa": 0.1
    })
    
    assert response.status_code == 200
    data = response.json()
    assert "gcode_path" in data
    assert data["calibration_type"] == "pressure_advance"
    assert "instructions" in data


def test_save_filament_calibration(client: TestClient, session: Session):
    """Test saving filament calibration."""
    response = client.post("/calibration/save", json={
        "printer_id": "test_printer",
        "filament_name": "esun_pla_red",
        "material_type": "PLA",
        "brand": "Esun",
        "color": "Red",
        "pressure_advance": 0.055,
        "optimal_nozzle_temp": 205.0,
        "optimal_bed_temp": 60.0,
        "flow_multiplier": 0.98
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["filament_name"] == "esun_pla_red"
    assert "filament_profile_id" in data


def test_get_filament_profiles(client: TestClient, session: Session):
    """Test retrieving filament profiles."""
    # Create a filament first
    client.post("/calibration/save", json={
        "printer_id": "test_printer",
        "filament_name": "test_filament",
        "material_type": "PLA",
        "pressure_advance": 0.05
    })
    
    response = client.get("/filaments/test_printer")
    assert response.status_code == 200
    data = response.json()
    assert len(data["filaments"]) > 0
