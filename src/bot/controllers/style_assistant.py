from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Preference, Recommendation, User, UserPhoto, UserProfile


@dataclass(slots=True)
class WeatherSnapshot:
    summary: str
    temperature_c: int
    warning: str | None


def _normalize(city: str) -> str:
    return city.strip().lower()


async def upsert_location(
    db_session: AsyncSession,
    user: User,
    *,
    city: str | None,
    lat: float | None,
    lon: float | None,
    allow_location: bool,
) -> UserProfile:
    stmt: Select[tuple[UserProfile]] = select(UserProfile).where(UserProfile.user_id == user.id)
    profile = (await db_session.execute(stmt)).scalar_one_or_none()
    if profile is None:
        profile = UserProfile(
            user_id=user.id,
            city=city,
            lat=Decimal(str(lat)) if lat is not None else None,
            lon=Decimal(str(lon)) if lon is not None else None,
            allow_location=allow_location,
        )
        db_session.add(profile)
    else:
        profile.city = city
        profile.lat = Decimal(str(lat)) if lat is not None else None
        profile.lon = Decimal(str(lon)) if lon is not None else None
        profile.allow_location = allow_location
    await db_session.flush()
    return profile


async def save_preference(db_session: AsyncSession, user: User, event_type: str, style: str) -> Preference:
    pref = Preference(user_id=user.id, event_type=event_type, style=style)
    db_session.add(pref)
    await db_session.flush()
    return pref


async def save_photo(db_session: AsyncSession, user: User, tg_file_id: str) -> UserPhoto:
    photo = UserPhoto(user_id=user.id, tg_file_id=tg_file_id)
    db_session.add(photo)
    await db_session.flush()
    return photo


async def generate_weather(city: str | None, lat: float | None, lon: float | None) -> WeatherSnapshot:
    if lat is None or lon is None:
        location = city or "вашему городу"
        return WeatherSnapshot(summary=f"Сейчас прохладно в {location}: около 14°C.", temperature_c=14, warning="Возможен дождь")

    pseudo_temp = int((abs(lat) + abs(lon)) % 30)
    warning = "Сильный ветер" if pseudo_temp < 10 else None
    return WeatherSnapshot(summary=f"Сейчас примерно {pseudo_temp}°C.", temperature_c=pseudo_temp, warning=warning)


def build_recommendations(event_type: str, style: str, weather: WeatherSnapshot) -> list[str]:
    base = {
        "повседневно": ["базовые джинсы", "хлопковая футболка", "кеды"],
        "мероприятие": ["брюки/юбка", "акцентный верх", "лоферы или каблук"],
    }
    style_piece = {
        "casual": "в расслабленном casual",
        "classic": "в аккуратном classic",
        "sport": "в функциональном sport",
    }
    pieces = ", ".join(base.get(event_type, base["повседневно"]))
    style_hint = style_piece.get(_normalize(style), f"в стиле {style}")

    return [
        f"1) {pieces}, {style_hint}",
        f"2) Добавь второй слой под {weather.temperature_c}°C (кардиган/пиджак)",
        "3) Выбери непромокаемую обувь, если есть риск осадков",
    ]


async def save_recommendation(
    db_session: AsyncSession,
    user: User,
    preference: Preference,
    weather_summary: str,
    message_text: str,
) -> Recommendation:
    rec = Recommendation(
        user_id=user.id,
        preference_id=preference.id,
        weather_summary=weather_summary,
        message_text=message_text,
    )
    db_session.add(rec)
    await db_session.flush()
    return rec


async def user_recommendation_history(db_session: AsyncSession, user: User, limit: int = 5) -> list[Recommendation]:
    stmt = (
        select(Recommendation)
        .where(Recommendation.user_id == user.id)
        .order_by(Recommendation.created_at.desc())
        .limit(limit)
    )
    return list((await db_session.execute(stmt)).scalars().all())


async def admin_metrics(db_session: AsyncSession) -> dict[str, int]:
    users_count = await db_session.scalar(select(func.count()).select_from(User))
    rec_count = await db_session.scalar(select(func.count()).select_from(Recommendation))
    photos_count = await db_session.scalar(select(func.count()).select_from(UserPhoto))
    return {
        "users": users_count or 0,
        "recommendations": rec_count or 0,
        "photos": photos_count or 0,
    }


def find_nearby_shops(city: str | None) -> list[str]:
    place = city or "вашем районе"
    return [
        f"Style Point — {place}",
        f"Urban Mood — {place}",
        f"Classic Hub — {place}",
    ]