import streamlit as st
from sqlalchemy import or_
from sqlalchemy.orm import Session

from src.database import SessionLocal
from src.models import Author, Poem, Tag
from src.page_helpers import initialize_app

st.set_page_config(page_title="Museu Virtual de Poesia", page_icon="📜", layout="wide")
initialize_app()

st.title("Galeria")
st.caption("Descubra poemas, autores e criações da comunidade.")

session: Session = SessionLocal()
try:
    tag_list = ["Todas"] + [tag.name for tag in session.query(Tag).order_by(Tag.name).all()]
    selected_tag = st.selectbox("Filtrar por tag", tag_list)
    search_value = st.text_input("Buscar por título ou autor")

    query = session.query(Poem).join(Author).filter(Poem.status == "publicado")
    if selected_tag != "Todas":
        query = query.join(Poem.tags).filter(Tag.name == selected_tag)
    if search_value:
        query = query.filter(
            or_(
                Poem.title.ilike(f"%{search_value}%"),
                Author.name.ilike(f"%{search_value}%"),
            )
        )

    poems = query.order_by(Poem.created_at.desc()).all()
    if not poems:
        st.info("Nenhum poema encontrado para os filtros atuais.")
    else:
        cols = st.columns(3)
        for index, poem in enumerate(poems):
            with cols[index % 3]:
                st.markdown(
                    f"""
                    <div style="padding: 1rem; border-radius: 12px; background: {'#f2f0ff' if index % 2 == 0 else '#ecfbff'}; border: 1px solid #d9d9d9; min-height: 220px;">
                        <h4>{poem.title}</h4>
                        <p><strong>{poem.author.name}</strong></p>
                        <p>{poem.body[:180].replace(chr(10), ' ')}</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                if st.button(f"Ler: {poem.title}", key=f"gallery_{poem.id}"):
                    st.session_state["selected_poem_id"] = poem.id
                    st.switch_page("pages/poems.py")
finally:
    session.close()
