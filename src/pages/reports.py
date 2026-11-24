import streamlit as st
from sqlalchemy.orm import Session

from src.database import SessionLocal
from src.models import Report
from src.page_helpers import initialize_app

initialize_app()
st.title("Denúncias e moderação")

session: Session = SessionLocal()
try:
    reports = session.query(Report).order_by(Report.created_at.desc()).all()
    if not reports:
        st.info("Nenhuma denúncia registrada.")

    for item in reports:
        st.markdown(f"### {item.poem.title}")
        st.write(f"Motivo: {item.reason}")
        st.write(f"Status atual: {item.status}")
        new_status = st.selectbox(
            "Alterar status",
            ["pendente", "em revisão", "aprovada", "removida"],
            key=f"report_status_{item.id}",
        )
        if st.button("Salvar status", key=f"save_report_{item.id}"):
            item.status = new_status
            session.commit()
            st.success("Status atualizado.")
            st.rerun()
finally:
    session.close()