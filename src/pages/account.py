import streamlit as st

from src.page_helpers import get_current_user, initialize_app

initialize_app()
st.title("Conta")

user = get_current_user()
if user is None:
    st.info("Entre ou crie uma conta para publicar textos e salvar seu histórico.")
    if st.button("Entrar ou cadastrar"):
        st.switch_page("pages/login.py")
else:
    st.success(f"Olá, {user.name}!")
    st.write(f"**E-mail:** {user.email}")
    st.write(f"**Biografia:** {user.bio or 'Nenhuma biografia cadastrada.'}")
    if st.button("Sair"):
        st.session_state.pop("user_id", None)
        st.rerun()