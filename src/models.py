from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, String, Table, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


poem_tags = Table(
    "poem_tags",
    Base.metadata,
    Column("poem_id", ForeignKey("poems.id"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id"), primary_key=True),
)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(150), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    bio: Mapped[Optional[str]] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    authors: Mapped[list["Author"]] = relationship(back_populates="user")
    poems: Mapped[list["Poem"]] = relationship(back_populates="published_by_user")
    reports: Mapped[list["Report"]] = relationship(back_populates="reporter")
    history: Mapped[list["ViewHistory"]] = relationship(back_populates="user")


class Author(Base):
    __tablename__ = "authors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    birth_date: Mapped[Optional[datetime]] = mapped_column(Date, nullable=True)
    death_date: Mapped[Optional[datetime]] = mapped_column(Date, nullable=True)
    bio: Mapped[Optional[str]] = mapped_column(Text, default="")
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    user: Mapped[Optional[User]] = relationship(back_populates="authors")
    poems: Mapped[list["Poem"]] = relationship(back_populates="author")

    __table_args__ = (UniqueConstraint("name", "user_id", name="uq_author_name_user"),)

class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)
    poems: Mapped[list["Poem"]] = relationship(secondary=poem_tags, back_populates="tags")

class Poem(Base):
    __tablename__ = "poems"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    slug: Mapped[str] = mapped_column(String(220), nullable=False, unique=True, index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="publicado")
    credit_type: Mapped[str] = mapped_column(String(50), nullable=False, default="autoral")
    source: Mapped[Optional[str]] = mapped_column(String(255), default="")
    rights_status: Mapped[str] = mapped_column(String(50), nullable=False, default="autoral")
    year_of_publication: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    translator: Mapped[Optional[str]] = mapped_column(String(200), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    author_id: Mapped[int] = mapped_column(ForeignKey("authors.id"), nullable=False)
    published_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    author: Mapped[Author] = relationship(back_populates="poems")
    published_by_user: Mapped[User] = relationship(back_populates="poems")
    tags: Mapped[list[Tag]] = relationship(secondary=poem_tags, back_populates="poems")
    reports: Mapped[list["Report"]] = relationship(back_populates="poem")
    history: Mapped[list["ViewHistory"]] = relationship(back_populates="poem")

class ViewHistory(Base):
    __tablename__ = "view_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    poem_id: Mapped[int] = mapped_column(ForeignKey("poems.id"), nullable=False)
    viewed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    user: Mapped[Optional[User]] = relationship(back_populates="history")
    poem: Mapped[Poem] = relationship(back_populates="history")

    __table_args__ = (UniqueConstraint("user_id", "poem_id", name="uq_user_poem_history"),)

class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    poem_id: Mapped[int] = mapped_column(ForeignKey("poems.id"), nullable=False)
    reporter_user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="pendente", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    poem: Mapped[Poem] = relationship(back_populates="reports")
    reporter: Mapped[Optional[User]] = relationship(back_populates="reports")
