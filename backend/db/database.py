"""
Database configuration and session management for SQLite.
Uses SQLAlchemy for ORM with a file-based SQLite database.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from pathlib import Path

# Database file location - stored in the db directory
DB_PATH = Path(__file__).parent / "adt.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

# Create engine with SQLite-specific settings
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # Required for SQLite with FastAPI
    echo=False  # Set to True for SQL query logging during development
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for declarative models
Base = declarative_base()


def init_db():
    """
    Initialize the database by creating all tables.
    Called on application startup.
    """
    from db import models  # Import models to register them with Base
    Base.metadata.create_all(bind=engine)
    _migrate_add_missing_columns()


def _migrate_add_missing_columns():
    """
    Lightweight schema migration for SQLite.

    create_all() only creates missing tables, not missing columns on
    tables that already exist. This project is small enough that a full
    migration tool (Alembic) would be overkill, so instead this diffs
    each model's declared columns against what's actually in the table
    and ALTER TABLEs in whatever is missing (e.g. a column added to a
    model after the table already existed on disk).
    """
    from sqlalchemy import inspect, text
    from sqlalchemy.schema import CreateColumn

    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())

    for table in Base.metadata.sorted_tables:
        if table.name not in existing_tables:
            continue  # create_all() already handles brand-new tables

        existing_columns = {col["name"] for col in inspector.get_columns(table.name)}
        for column in table.columns:
            if column.name in existing_columns:
                continue
            ddl = str(CreateColumn(column).compile(dialect=engine.dialect))
            with engine.begin() as conn:
                conn.execute(text(f"ALTER TABLE {table.name} ADD COLUMN {ddl}"))


def get_db():
    """
    Dependency that provides a database session.
    Ensures proper cleanup after request completion.

    Usage:
        @app.get("/example")
        def example(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
