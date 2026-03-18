from __future__ import annotations

import os
from urllib.parse import urlparse

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config import get_settings


settings = get_settings()

connect_args = {}
if settings.db_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(settings.db_url, future=True, pool_pre_ping=True, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def init_db() -> None:
    from .models import Base  # noqa: WPS433 (import inside for init order)

    if settings.db_url.startswith("sqlite"):
        # Ensure parent directory exists for sqlite file paths like sqlite:///./data/app.db
        parsed = urlparse(settings.db_url)
        db_path = (parsed.path or "").lstrip("/")
        if db_path:
            parent = os.path.dirname(db_path)
            if parent:
                os.makedirs(parent, exist_ok=True)

    Base.metadata.create_all(bind=engine)

