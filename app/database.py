from sqlmodel import SQLModel, create_engine, Session
from typing import Generator
import os
from dotenv import load_dotenv

load_dotenv()

# Default to SQLite, but allow database URL override for Postgres/Supabase
database_url = os.getenv("DATABASE_URL", "sqlite:///./baseball_league.db")

# Create engine
engine = create_engine(database_url, connect_args={"check_same_thread": False} if "sqlite" in database_url else {})


def create_db_and_tables():
    """Create all database tables."""
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    """Dependency for FastAPI to get database sessions."""
    with Session(engine) as session:
        yield session

