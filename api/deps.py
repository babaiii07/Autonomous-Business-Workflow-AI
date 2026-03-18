from __future__ import annotations

from collections.abc import Generator

from tools.db import SessionLocal, init_db


def get_db() -> Generator:
    init_db()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

