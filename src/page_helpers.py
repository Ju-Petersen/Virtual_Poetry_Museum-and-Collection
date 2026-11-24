from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from typing import Optional

import streamlit as st
from sqlalchemy.orm import Session

from src.database import SessionLocal, create_database, ensure_demo_data
from src.models import Poem, User, ViewHistory


def initialize_app() -> None:
    create_database()
    ensure_demo_data()


def slugify(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")


def hash_password(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def get_current_user() -> Optional[User]:
    user_id = st.session_state.get("user_id")
    if not user_id:
        return None

    session: Session = SessionLocal()
    try:
        return session.get(User, user_id)
    finally:
        session.close()


def record_view(poem: Poem, user: Optional[User]) -> None:
    if user is None:
        return

    session: Session = SessionLocal()
    try:
        existing = session.query(ViewHistory).filter_by(user_id=user.id, poem_id=poem.id).first()
        if existing:
            existing.viewed_at = datetime.now(timezone.utc)
        else:
            session.add(ViewHistory(user_id=user.id, poem_id=poem.id, viewed_at=datetime.now(timezone.utc)))
        session.commit()
    finally:
        session.close()
