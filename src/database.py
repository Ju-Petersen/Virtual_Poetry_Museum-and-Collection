from __future__ import annotations

from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.config import get_database_url
from src.models import Author, Base, Poem, Report, Tag, User, ViewHistory


def get_engine():
    database_url = get_database_url()
    if database_url.startswith("sqlite"):
        return create_engine(database_url, connect_args={"check_same_thread": False})
    return create_engine(database_url, pool_pre_ping=True)


engine = get_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def create_database() -> None:
    Base.metadata.create_all(bind=engine)


def ensure_demo_data() -> None:
    session: Session = SessionLocal()
    try:
        if session.query(User).count() > 0:
            return

        user = User(
            name="Ana Leal",
            email="ana@email.com",
            password_hash="demo-hash",
            bio="Curiosa por poesia e memória.",
        )
        session.add(user)
        session.flush()

        author = Author(
            name="Cecília Meireles",
            bio="Poetisa brasileira que marcou a literatura moderna.",
            user_id=user.id,
        )
        session.add(author)
        session.flush()

        tag1 = Tag(name="amor")
        tag2 = Tag(name="memória")
        tag3 = Tag(name="vida")
        session.add_all([tag1, tag2, tag3])
        session.flush()

        poem1 = Poem(
            title="Voz de Muitas Cidades",
            body="Noite\n\nO vento passa pelo corredor\ncomo se escrevesse em silêncio\nmeu nome nas janelas.\n\nEu escuto a cidade\nrespirando em versos.",
            slug="voz-de-muitas-cidades",
            status="publicado",
            credit_type="autoral",
            source="Original",
            rights_status="autoral",
            year_of_publication=2024,
            author_id=author.id,
            published_by_user_id=user.id,
        )
        poem1.tags.extend([tag1, tag2])

        poem2 = Poem(
            title="Poema do Silêncio",
            body="Silêncio\n\nNão grita, não pesa,\nmas mora no fundo dos quartos\nque a vida deixa vazios.\n\nE, mesmo assim,\nensina a ouvir.",
            slug="poema-do-silencio",
            status="rascunho",
            credit_type="de-terceiro",
            source="Acervo comunitário",
            rights_status="dominio-publico",
            author_id=author.id,
            published_by_user_id=user.id,
        )
        poem2.tags.append(tag3)

        session.add_all([poem1, poem2])
        session.commit()
    finally:
        session.close()


def add_demo_view(user_id: int, poem_id: int) -> None:
    session: Session = SessionLocal()
    try:
        existing = session.query(ViewHistory).filter_by(user_id=user_id, poem_id=poem_id).first()
        if existing:
            existing.viewed_at = datetime.utcnow()
        else:
            session.add(ViewHistory(user_id=user_id, poem_id=poem_id, viewed_at=datetime.utcnow()))
        session.commit()
    finally:
        session.close()


def create_report(poem_id: int, reason: str, reporter_user_id: int | None = None) -> None:
    session: Session = SessionLocal()
    try:
        report = Report(poem_id=poem_id, reason=reason, reporter_user_id=reporter_user_id)
        session.add(report)
        session.commit()
    finally:
        session.close()
