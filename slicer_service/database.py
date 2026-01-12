"""Database initialization and session management."""
from sqlmodel import SQLModel, create_engine, Session
from .config import DATABASE_PATH

# Create engine
engine = create_engine(f"sqlite:///{DATABASE_PATH}", echo=False)


def init_db():
    """Initialize database tables."""
    SQLModel.metadata.create_all(engine)


def get_session():
    """Get database session."""
    with Session(engine) as session:
        yield session
