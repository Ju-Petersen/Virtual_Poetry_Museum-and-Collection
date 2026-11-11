from __future__ import annotations # 

import hashlib # 
import re # 
import sys # 
from datetime import datetime, timezone
from pathlib import Path # 
from typing import Optional

import streamlit as st
from sqlalchemy import func
from sqlalchemy.orm import Session

PROJECT_ROOT = Path(__file__).resolve().parent.parent # 
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.database import SessionLocal, create_database, create_report, ensure_demo_data
from src.models import Author, Poem, Report, Tag, User, ViewHistory

st.set_page_config(page_title="Museu Virtual de Poesia", page_icon="📜", layout="wide")

def slugify(value: str) -> str: # 
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

def render_gallery() -> None:
    session: Session = SessionLocal()
    try:
        st.title("Galeria")
        st.caption("Descubra poemas, autores e criações da comunidade.")

        tag_list = ["Todas"] + [tag.name for tag in session.query(Tag).order_by(Tag.name).all()]
        selected_tag = st.selectbox("Filtrar por tag", tag_list)
        search_value = st.text_input("Buscar por título ou autor")

        query = session.query(Poem).join(Author).filter(Poem.status == "publicado")
        if selected_tag != "Todas":
            query = query.join(Poem.tags).filter(Tag.name == selected_tag)
        if search_value:
            query = query.filter((Poem.title.ilike(f"%{search_value}%")) | (Author.name.ilike(f"%{search_value}%")))

        poems = query.order_by(Poem.created_at.desc()).all()

        if not poems:
            st.info("Nenhum poema encontrado para os filtros atuais.")
            return

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
                    st.switch_page("pages/poems.py")
                    # Separar as guias (renderização de poemas, login, publicar, etc, 
                    # que estão em definições neste arquivo) 
                    # em páginas diferentes no diretório "pages" para possibilitar um "multipage app".
                    st.session_state["selected_poem_id"] = poem.id
                    st.session_state["page"] = "Poema"
                    st.rerun()
    finally:
        session.close()

def render_poem_page() -> None:
    session: Session = SessionLocal()
    try:
        poem_id = st.session_state.get("selected_poem_id")
        if poem_id is None:
            poem = session.query(Poem).filter(Poem.status == "publicado").order_by(Poem.created_at.desc()).first()
            if poem is None:
                st.warning("Ainda não há poemas publicados.")
                return
            poem_id = poem.id

        poem = session.get(Poem, poem_id)
        if poem is None:
            st.warning("Poema não encontrado.")
            return

        user = get_current_user()
        record_view(poem, user)

        st.title(poem.title)
        st.caption(f"Autor original: {poem.author.name} | Publicado por: {poem.published_by_user.name}")
        if poem.tags:
            st.caption(f"Tags: {' | '.join(tag.name for tag in poem.tags)}")

        st.markdown(poem.body.replace("\n\n", "<br><br>").replace("\n", "<br>"), unsafe_allow_html=True)

        st.subheader("Outros poemas do autor")
        others = session.query(Poem).filter(Poem.author_id == poem.author_id, Poem.id != poem.id, Poem.status == "publicado").order_by(Poem.created_at.desc()).limit(5).all()
        if others:
            for item in others:
                if st.button(item.title, key=f"poem_more_{item.id}"):
                    st.session_state["selected_poem_id"] = item.id
                    st.rerun()
        else:
            st.write("Este autor ainda não tem mais textos públicos.")

        if st.button("Denunciar / solicitar remoção"):
            create_report(poem.id, "Solicitação de remoção por usuário da plataforma.", user.id if user else None)
            st.success("Denúncia registrada para revisão da moderação.")
    finally:
        session.close()

def render_publish_page() -> None:
    user = get_current_user()
    if user is None:
        st.warning("Faça login antes de publicar um poema.")
        return

    session: Session = SessionLocal()
    try:
        authors = session.query(Author).order_by(Author.name).all()
        choices = [author.name for author in authors] + ["Novo autor"]

        with st.form("publish_form"):
            st.title("Publicar poema")

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
            year_of_publication = st.number_input("Ano de publicação original", min_value=0, max_value=2100, value=2024)

            submitted = st.form_submit_button("Salvar poema")
            if submitted:
                if not title or not body:
                    st.error("Título e texto são obrigatórios.")
                    return
                if not rights_checkbox:
                    st.error("Você precisa confirmar a autorização para publicação.")
                    return

                if new_author_name:
                    author = session.query(Author).filter(func.lower(Author.name) == new_author_name.lower()).first()
                    if author is None:
                        author = Author(name=new_author_name, bio="Autor cadastrado pela comunidade.", user_id=user.id)
                        session.add(author)
                        session.flush()
                else:
                    author = next((item for item in authors if item.name == author_name), None)
                    if author is None:
                        st.error("Selecione um autor válido.")
                        return

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
                    tag = session.query(Tag).filter(func.lower(Tag.name) == tag_name.lower()).first()
                    if tag is None:
                        tag = Tag(name=tag_name)
                        session.add(tag)
                        session.flush()
                    poem.tags.append(tag)

                session.commit()
                st.success("Poema salvo com sucesso.")
    finally:
        session.close()

def render_my_texts() -> None:
    user = get_current_user()
    if user is None:
        st.warning("Você precisa estar logado para visualizar seus textos.")
        return

    session: Session = SessionLocal()
    try:
        poems = session.query(Poem).filter(Poem.published_by_user_id == user.id).order_by(Poem.updated_at.desc()).all()
        if not poems:
            st.info("Você ainda não tem textos publicados.")
            return

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
                    status = st.selectbox("Status", ["rascunho", "publicado", "oculto"], index=["rascunho", "publicado", "oculto"].index(poem.status))
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

def render_history() -> None:
    user = get_current_user()
    session: Session = SessionLocal()
    try:
        st.title("Histórico")
        if user is None:
            st.info("Acesse a conta para salvar seu histórico de leitura.")
            return

        history = session.query(ViewHistory).filter(ViewHistory.user_id == user.id).order_by(ViewHistory.viewed_at.desc()).all()
        if not history:
            st.info("Você ainda não visitou textos.")
            return

        for item in history:
            poem = item.poem
            if st.button(f"{poem.title} — {poem.author.name}", key=f"hist_{item.id}"):
                st.session_state["selected_poem_id"] = poem.id
                st.session_state["page"] = "Poema"
                st.rerun()
    finally:
        session.close()

def render_account() -> None:
    st.title("Conta")

    user = get_current_user()
    if user:
        st.success(f"Olá, {user.name}!")
        if st.button("Sair"):
            st.session_state.pop("user_id", None)
            st.rerun()
        return

    tab_login, tab_register = st.tabs(["Login", "Cadastro"])

    with tab_login:
        with st.form("login_form"):
            email = st.text_input("E-mail")
            password = st.text_input("Senha", type="password")
            submitted = st.form_submit_button("Entrar")
            if submitted:
                session: Session = SessionLocal()
                try:
                    found = session.query(User).filter_by(email=email.strip().lower()).first()
                    if found and found.password_hash == hash_password(password):
                        st.session_state["user_id"] = found.id
                        st.success("Login realizado com sucesso.")
                        st.rerun()
                    else:
                        st.error("Credenciais inválidas.")
                finally:
                    session.close()

    with tab_register:
        with st.form("register_form"):
            name = st.text_input("Nome")
            email = st.text_input("E-mail")
            password = st.text_input("Senha", type="password")
            bio = st.text_area("Biografia")
            submitted = st.form_submit_button("Cadastrar")
            if submitted:
                if not name or not email or not password:
                    st.error("Preencha nome, e-mail e senha.")
                    return
                session: Session = SessionLocal()
                try:
                    if session.query(User).filter_by(email=email.strip().lower()).first():
                        st.error("Já existe um usuário com esse e-mail.")
                    else:
                        session.add(User(name=name, email=email.strip().lower(), password_hash=hash_password(password), bio=bio))
                        session.commit()
                        st.success("Cadastro realizado. Faça login.")
                finally:
                    session.close()

def render_author_crud() -> None:
    session: Session = SessionLocal()
    try:
        st.title("Autores")
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

def render_user_crud() -> None:
    session: Session = SessionLocal()
    try:
        st.title("Usuários")
        users = session.query(User).order_by(User.name).all()
        selected_name = st.selectbox("Usuário", ["Novo"] + [user.name for user in users])

        if selected_name == "Novo":
            name = st.text_input("Nome")
            email = st.text_input("E-mail")
            password = st.text_input("Senha", type="password")
            bio = st.text_area("Biografia")
            if st.button("Criar usuário"):
                if name and email and password:
                    session.add(User(name=name, email=email.strip().lower(), password_hash=hash_password(password), bio=bio))
                    session.commit()
                    st.success("Usuário criado.")
                    st.rerun()
        else:
            user = next(item for item in users if item.name == selected_name)
            name = st.text_input("Nome", value=user.name)
            email = st.text_input("E-mail", value=user.email)
            bio = st.text_area("Biografia", value=user.bio or "")
            if st.button("Atualizar usuário"):
                user.name = name
                user.email = email.strip().lower()
                user.bio = bio
                session.commit()
                st.success("Usuário atualizado.")
                st.rerun()
            if st.button("Excluir usuário"):
                session.delete(user)
                session.commit()
                st.success("Usuário excluído.")
                st.rerun()
    finally:
        session.close()

def render_poem_crud() -> None:
    session: Session = SessionLocal()
    try:
        st.title("Poemas")
        poems = session.query(Poem).order_by(Poem.created_at.desc()).all()
        selected = st.selectbox("Poema", ["Novo"] + [f"{poem.id} - {poem.title}" for poem in poems])
        if selected == "Novo":
            st.info("Use a página de Publicar para criar um novo poema.")
            return

        poem = next(item for item in poems if f"{item.id} - {item.title}" == selected)
        title = st.text_input("Título", value=poem.title)
        body = st.text_area("Texto", value=poem.body, height=220)
        status = st.selectbox("Status", ["rascunho", "publicado", "oculto"], index=["rascunho", "publicado", "oculto"].index(poem.status))

        if st.button("Salvar alterações"):
            poem.title = title
            poem.body = body
            poem.status = status
            poem.slug = slugify(title)
            poem.updated_at = datetime.utcnow()
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

def render_tag_crud() -> None:
    session: Session = SessionLocal()
    try:
        st.title("Tags")
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

def render_reports() -> None:
    session: Session = SessionLocal()
    try:
        st.title("Denúncias e moderação")
        reports = session.query(Report).order_by(Report.created_at.desc()).all()
        if not reports:
            st.info("Nenhuma denúncia registrada.")
            return

        for item in reports:
            st.markdown(f"### {item.poem.title}")
            st.write(f"Motivo: {item.reason}")
            st.write(f"Status atual: {item.status}")
            new_status = st.selectbox("Alterar status", ["pendente", "em revisão", "aprovada", "removida"], key=f"report_status_{item.id}")
            if st.button("Salvar status", key=f"save_report_{item.id}"):
                item.status = new_status
                session.commit()
                st.success("Status atualizado.")
                st.rerun()
    finally:
        session.close()

def main() -> None:
    create_database()
    ensure_demo_data()

    pages = ["Galeria", "Poema", "Publicar", "Meus textos", "Histórico", "Conta", "Autores", "Usuários", "Poemas", "Tags", "Denúncias"]
    page = st.sidebar.radio("Navegação", pages, index=0)
    st.session_state["page"] = page

    if page == "Galeria":
        render_gallery()
    elif page == "Poema":
        render_poem_page()
    elif page == "Publicar":
        render_publish_page()
    elif page == "Meus textos":
        render_my_texts()
    elif page == "Histórico":
        render_history()
    elif page == "Conta":
        render_account()
    elif page == "Autores":
        render_author_crud()
    elif page == "Usuários":
        render_user_crud()
    elif page == "Poemas":
        render_poem_crud()
    elif page == "Tags":
        render_tag_crud()
    else:
        render_reports()

if __name__ == "__main__":
    main()
