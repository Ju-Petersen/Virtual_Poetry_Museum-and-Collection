import streamlit as st
from sqlalchemy.orm import Session

from src.database import SessionLocal
from src.models import Poem
from src.page_helpers import initialize_app, slugify

initialize_app()
st.title("Poemas")

session: Session = SessionLocal()
try:
    poems = session.query(Poem).order_by(Poem.created_at.desc()).all()
    selected = st.selectbox("Poema", ["Novo"] + [f"{poem.id} - {poem.title}" for poem in poems])
    if selected == "Novo":
        st.info("Use a página de Publicar para criar um novo poema.")
    else:
        poem = next(item for item in poems if f"{item.id} - {item.title}" == selected)
        title = st.text_input("Título", value=poem.title)
        body = st.text_area("Texto", value=poem.body, height=220)
        status_options = ["rascunho", "publicado", "oculto"]
        status = st.selectbox("Status", status_options, index=status_options.index(poem.status))

        if st.button("Salvar alterações"):
            poem.title = title
            poem.body = body
            poem.status = status
            poem.slug = slugify(title)
            session.commit()
            st.success("Poema atualizado.")
            st.rerun()

        if st.button("Excluir poema"):
            session.delete(poem)
            session.commit()
            st.success("Poema excluído.")
            st.rerun()
finally:
    session.close()