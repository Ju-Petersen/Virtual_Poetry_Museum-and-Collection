from datetime import datetime

import streamlit as st
from sqlalchemy.orm import Session

from src.database import SessionLocal
from src.models import Poem
from src.page_helpers import get_current_user, initialize_app, slugify

initialize_app()
st.title("Meus textos")

user = get_current_user()
if user is None:
    st.warning("Você precisa estar logado para visualizar seus textos.")
else:
    session: Session = SessionLocal()
    try:
        poems = (
            session.query(Poem)
            .filter(Poem.published_by_user_id == user.id)
            .order_by(Poem.updated_at.desc())
            .all()
        )
        if not poems:
            st.info("Você ainda não tem textos publicados.")

        for poem in poems:
            st.markdown(f"### {poem.title}")
            st.caption(f"Status: {poem.status} | Atualizado em {poem.updated_at:%d/%m/%Y %H:%M}")
            st.write(poem.body[:220] + ("..." if len(poem.body) > 220 else ""))

            cols = st.columns(3)
            with cols[0]:
                if st.button("Editar", key=f"edit_{poem.id}"):
                    st.session_state["editing_poem_id"] = poem.id
            with cols[1]:
                if st.button("Ocultar", key=f"hide_{poem.id}"):
                    poem.status = "oculto"
                    session.commit()
                    st.rerun()
            with cols[2]:
                if st.button("Excluir", key=f"delete_{poem.id}"):
                    session.delete(poem)
                    session.commit()
                    st.rerun()

            if st.session_state.get("editing_poem_id") == poem.id:
                with st.form(f"edit_form_{poem.id}"):
                    title = st.text_input("Título", value=poem.title)
                    body = st.text_area("Texto", value=poem.body, height=180)
                    status_options = ["rascunho", "publicado", "oculto"]
                    status = st.selectbox(
                        "Status",
                        status_options,
                        index=status_options.index(poem.status),
                    )
                    if st.form_submit_button("Salvar alterações"):
                        poem.title = title
                        poem.body = body
                        poem.status = status
                        poem.slug = slugify(title)
                        poem.updated_at = datetime.utcnow()
                        session.commit()
                        st.session_state.pop("editing_poem_id", None)
                        st.success("Poema atualizado.")
                        st.rerun()
    finally:
        session.close()