from sqlalchemy import BigInteger, String, Text, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class PosterTemplate(Base):
    """海报模板"""
    __tablename__ = "poster_templates"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    layout: Mapped[str] = mapped_column(String(32), default="vertical")
    background_color: Mapped[str] = mapped_column(String(16), default="#1a1a2e")
    text_color: Mapped[str] = mapped_column(String(16), default="#ffffff")
    accent_color: Mapped[str] = mapped_column(String(16), default="#e94560")
    columns: Mapped[int] = mapped_column(Integer, default=3)
    show_rating: Mapped[bool] = mapped_column(default=True)
    show_year: Mapped[bool] = mapped_column(default=True)
    show_genres: Mapped[bool] = mapped_column(default=False)
    cover_text: Mapped[str | None] = mapped_column(String(256), nullable=True)


class GeneratedPoster(Base):
    """已生成的海报"""
    __tablename__ = "generated_posters"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    template_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    item_ids: Mapped[list | None] = mapped_column(JSON, nullable=True)
    image_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    html_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="generated")
