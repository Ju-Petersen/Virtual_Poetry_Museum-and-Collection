import streamlit as st
from sqlalchemy import func
from sqlalchemy.orm import Session

from src.database import SessionLocal
from src.models import Author, Poem, Tag
from src.page_helpers import get_current_user, initialize_app, slugify

initialize_app()
st.title("Publicar poema")

user = get_current_user()
if user is None:
    st.warning("Faça login antes de publicar um poema.")
else:
    session: Session = SessionLocal()
    try:
        authors = session.query(Author).order_by(Author.name).all()
        choices = [author.name for author in authors] + ["Novo autor"]

        with st.form("publish_form"):
            title = st.text_input("Título")
            body = st.text_area("Texto", height=240, help="Preserve quebras de linha e espaços.")
            tags_input = st.text_input("Tags (separadas por vírgula)")
            author_name = st.selectbox("Autor original", choices)
            if author_name == "Novo autor":
                new_author_name = st.text_input("Nome do autor")
            else:
                new_author_name = ""

            rights_checkbox = st.checkbox("Declaro que tenho direito de publicar este texto.")
            status = st.selectbox("Status", ["rascunho", "publicado", "oculto"])
            credit_type = st.selectbox("Tipo de obra", ["autoral", "de-terceiro", "tradução"])
            source = st.text_input("Fonte / referência")
            rights_status = st.selectbox("Situação de direitos", ["autoral", "dominio-publico", "autorizacao"])
            year_of_publication = st.number_input(
                "Ano de publicação original",
                min_value=0,
                max_value=2100,
                value=2024,
            )

            submitted = st.form_submit_button("Salvar poema")
            if submitted:
                if not title or not body:
                    st.error("Título e texto são obrigatórios.")
                elif not rights_checkbox:
                    st.error("Você precisa confirmar a autorização para publicação.")
                else:
                    if new_author_name:
                        author = (
                            session.query(Author)
                            .filter(func.lower(Author.name) == new_author_name.lower())
                            .first()
                        )
                        if author is None:
                            author = Author(
                                name=new_author_name,
                                bio="Autor cadastrado pela comunidade.",
                                user_id=user.id,
                            )
                            session.add(author)
                            session.flush()
                    else:
                        author = next((item for item in authors if item.name == author_name), None)
                        if author is None:
                            st.error("Selecione um autor válido.")
                            st.stop()

                    poem = Poem(
                        title=title,
                        body=body,
                        slug=slugify(title),
                        status=status,
                        credit_type=credit_type,
                        source=source,
                        rights_status=rights_status,
                        year_of_publication=year_of_publication,
                        author_id=author.id,
                        published_by_user_id=user.id,
                    )
                    session.add(poem)
                    session.flush()

                    for tag_name in [part.strip() for part in tags_input.split(",") if part.strip()]:
                        tag = (
                            session.query(Tag)
                            .filter(func.lower(Tag.name) == tag_name.lower())
                            .first()
                        )
                        if tag is None:
                            tag = Tag(name=tag_name)
                            session.add(tag)
                            session.flush()
                        poem.tags.append(tag)

                    session.commit()
                    st.success("Poema salvo com sucesso.")
    finally:
        session.close()