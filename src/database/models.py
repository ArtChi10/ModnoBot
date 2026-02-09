from datetime import datetime
from sqlalchemy import BOOLEAN, BigInteger, DateTime, ForeignKey, Integer, Numeric, Text, TIMESTAMP, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    __abstract__ = True
    __table_args__ = {"extend_existing": True}

    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class User(Base):
    __tablename__ = "users"

    tg_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    fullname: Mapped[str]
    username: Mapped[str]
    ai_thread: Mapped[str | None]
    action_count: Mapped[int] = mapped_column(Integer, default=0)
    is_context_added: Mapped[bool] = mapped_column(BOOLEAN, default=False)
    space: Mapped[str | None]
    geography: Mapped[str | None]
    request: Mapped[str | None]
    source: Mapped[str | None]

    def __str__(self) -> str:
        return f"{self.__class__.__name__}(id: {self.tg_id}, fullname: {self.fullname})"

    def __repr__(self) -> str:
        return str(self)


class UserProfile(Base):
    __tablename__ = "user_profile"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True)
    city: Mapped[str | None]
    lat: Mapped[float | None] = mapped_column(Numeric(10, 6))
    lon: Mapped[float | None] = mapped_column(Numeric(10, 6))
    allow_location: Mapped[bool] = mapped_column(BOOLEAN, default=False, server_default="false")
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Preference(Base):
    __tablename__ = "preferences"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    event_type: Mapped[str]
    style: Mapped[str]
    season_bias: Mapped[str | None]


class UserPhoto(Base):
    __tablename__ = "photos"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    tg_file_id: Mapped[str]


class Recommendation(Base):
    __tablename__ = "recommendations"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    preference_id: Mapped[int | None] = mapped_column(ForeignKey("preferences.id", ondelete="SET NULL"))
    weather_summary: Mapped[str]
    message_text: Mapped[str]


class UserCounters(Base):
    __tablename__ = "user_counters"

    tg_id: Mapped[int] = mapped_column(ForeignKey("users.tg_id", ondelete="CASCADE"))
    period_started_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    image_count: Mapped[int] = mapped_column(Integer, default=0)


class PlantAnalysis(Base):
    __tablename__ = "plant_analyses"

    user_tg_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.tg_id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    thread_id: Mapped[str | None]

    tg_file_id: Mapped[str] = mapped_column(nullable=False)
    tg_file_unique_id: Mapped[str | None]

    ai_response: Mapped[str] = mapped_column(Text, nullable=False)
    health_score: Mapped[int | None] = mapped_column(Integer)