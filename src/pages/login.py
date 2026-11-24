import streamlit as st
from sqlalchemy.orm import Session

from src.database import SessionLocal
from src.models import User
from src.page_helpers import hash_password, initialize_app

initialize_app()
st.title("Entrar ou criar conta")

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
            else:
                session: Session = SessionLocal()
                try:
                    if session.query(User).filter_by(email=email.strip().lower()).first():
                        st.error("Já existe um usuário com esse e-mail.")
                    else:
                        session.add(
                            User(
                                name=name,
                                email=email.strip().lower(),
                                password_hash=hash_password(password),
                                bio=bio,
                            )
                        )
                        session.commit()
                        st.success("Cadastro realizado. Faça login.")
                finally:
                    session.close()