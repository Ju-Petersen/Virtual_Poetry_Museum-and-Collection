import streamlit as st
from sqlalchemy.orm import Session

from src.database import SessionLocal
from src.models import Tag
from src.page_helpers import initialize_app

initialize_app()
st.title("Tags")

session: Session = SessionLocal()
try:
    tags = session.query(Tag).order_by(Tag.name).all()
    selected = st.selectbox("Tag", ["Nova"] + [tag.name for tag in tags])

    if selected == "Nova":
        name = st.text_input("Nome da nova tag")
        if st.button("Criar tag"):
            if name:
                session.add(Tag(name=name))
                session.commit()
                st.success("Tag criada.")
                st.rerun()
    else:
        tag = next(item for item in tags if item.name == selected)
        name = st.text_input("Nome da tag", value=tag.name)
        if st.button("Atualizar tag"):
            tag.name = name
            session.commit()
            st.success("Tag atualizada.")
            st.rerun()
        if st.button("Excluir tag"):
            session.delete(tag)
            session.commit()
            st.success("Tag excluída.")
            st.rerun()
finally:
    session.close()