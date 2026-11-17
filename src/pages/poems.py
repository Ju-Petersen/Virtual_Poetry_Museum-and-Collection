import streamlit as st
from sqlalchemy import func
from sqlalchemy.orm import Session

from src.database import SessionLocal
from src.models import Author, Poem

session: Session = SessionLocal()

st.title("Poemas")

poem_id = st.session_state.get("selected_poem_id")
    if poem_id is None:
        poem = session.query(Poem).filter(Poem.status == "publicado").order_by(Poem.created_at.desc()).first()
        if poem is None:
            st.warning("Ainda não há poemas publicados.")
            poem_id = poem.id

    poem = session.get(Poem, poem_id)
