import streamlit as st
from sqlalchemy.orm import Session

from src.database import SessionLocal
from src.models import Author
from src.page_helpers import initialize_app

initialize_app()
st.title("Autores")

session: Session = SessionLocal()
try:
    author_list = session.query(Author).order_by(Author.name).all()
    selected_name = st.selectbox("Autor", ["Novo"] + [author.name for author in author_list])

    if selected_name == "Novo":
        name = st.text_input("Nome do autor")
        bio = st.text_area("Bio")
        if st.button("Criar autor"):
            if name:
                session.add(Author(name=name, bio=bio))
                session.commit()
                st.success("Autor criado.")
                st.rerun()
    else:
        author = next(item for item in author_list if item.name == selected_name)
        name = st.text_input("Nome", value=author.name)
        bio = st.text_area("Bio", value=author.bio or "")
        if st.button("Atualizar autor"):
            author.name = name
            author.bio = bio
            session.commit()
            st.success("Autor atualizado.")
            st.rerun()
        if st.button("Excluir autor"):
            session.delete(author)
            session.commit()
            st.success("Autor excluído.")
            st.rerun()
finally:
    session.close()