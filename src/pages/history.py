import streamlit as st
from sqlalchemy.orm import Session

from src.database import SessionLocal
from src.models import ViewHistory
from src.page_helpers import get_current_user, initialize_app

initialize_app()
st.title("Histórico")

user = get_current_user()
session: Session = SessionLocal()
try:
    if user is None:
        st.info("Acesse a conta para salvar seu histórico de leitura.")
    else:
        history = (
            session.query(ViewHistory)
            .filter(ViewHistory.user_id == user.id)
            .order_by(ViewHistory.viewed_at.desc())
            .all()
        )
        if not history:
            st.info("Você ainda não visitou textos.")

        for item in history:
            poem = item.poem
            if st.button(f"{poem.title} — {poem.author.name}", key=f"hist_{item.id}"):
                st.session_state["selected_poem_id"] = poem.id
                st.switch_page("pages/poems.py")
finally:
    session.close()