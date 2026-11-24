import streamlit as st
from sqlalchemy.orm import Session

from src.database import SessionLocal, create_report
from src.models import Poem
from src.page_helpers import get_current_user, initialize_app, record_view

initialize_app()

session: Session = SessionLocal()
try:
    poem_id = st.session_state.get("selected_poem_id")
    if poem_id is None:
        poem = (
            session.query(Poem)
            .filter(Poem.status == "publicado")
            .order_by(Poem.created_at.desc())
            .first()
        )
        if poem is None:
            st.warning("Ainda não há poemas publicados.")
        else:
            poem_id = poem.id

    poem = session.get(Poem, poem_id) if poem_id is not None else None
    if poem is not None:
        user = get_current_user()
        record_view(poem, user)

        st.title(poem.title)
        st.caption(f"Autor original: {poem.author.name} | Publicado por: {poem.published_by_user.name}")
        if poem.tags:
            st.caption(f"Tags: {' | '.join(tag.name for tag in poem.tags)}")

        st.markdown(poem.body.replace("\n\n", "<br><br>").replace("\n", "<br>"), unsafe_allow_html=True)

        st.subheader("Outros poemas do autor")
        others = (
            session.query(Poem)
            .filter(
                Poem.author_id == poem.author_id,
                Poem.id != poem.id,
                Poem.status == "publicado",
            )
            .order_by(Poem.created_at.desc())
            .limit(5)
            .all()
        )
        if others:
            for item in others:
                if st.button(item.title, key=f"poem_more_{item.id}"):
                    st.session_state["selected_poem_id"] = item.id
                    st.rerun()
        else:
            st.write("Este autor ainda não tem mais textos públicos.")

        if st.button("Denunciar / solicitar remoção"):
            create_report(
                poem.id,
                "Solicitação de remoção por usuário da plataforma.",
                user.id if user else None,
            )
            st.success("Denúncia registrada para revisão da moderação.")
    elif poem_id is not None:
        st.warning("Poema não encontrado.")
finally:
    session.close()
