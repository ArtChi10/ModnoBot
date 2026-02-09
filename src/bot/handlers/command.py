from aiogram import F, Router
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import Settings
from bot.controllers.style_assistant import (
    admin_metrics,
    build_recommendations,
    find_nearby_shops,
    generate_weather,
    save_photo,
    save_preference,
    save_recommendation,
    upsert_location,
    user_recommendation_history,
)
from bot.internal.enums import StyleAssistantState
from bot.internal.keyboards import (
    event_kb,
    location_request_kb,
    photo_optional_kb,
    shops_kb,
    start_selection_kb,
    style_kb,
)
from database.models import User
router = Router()


@router.message(Command("start", "help", "history", "admin_logs", "admin_catalog"))
async def command_handler(
    message: Message,
    command: CommandObject,
    user: User,
    settings: Settings,
    state: FSMContext,
    db_session: AsyncSession,
) -> None:
    match command.command:
        case "start":
            await state.set_state(StyleAssistantState.ONBOARDING_START)
            await message.answer(
                "Привет! Я Style Assistant Bot 👗\n"
                "Подберу образ с учетом события, стиля и погоды.",
                reply_markup=start_selection_kb(),
            )
        case "help":
            await message.answer(
                "Команды:\n"
                "/start — начать подбор\n"
                "/history — история последних подборок\n"
                "/admin_logs — метрики (для админа)\n"
                "/admin_catalog — управление каталогом (заглушка)"
            )
        case "history":
            history = await user_recommendation_history(db_session, user)
            if not history:
                await message.answer("История подборок пока пуста. Нажми /start")
                return
            lines = ["Ваши последние подборки:"]
            for item in history:
                lines.append(f"• {item.created_at:%d.%m %H:%M} — {item.weather_summary}")
            await message.answer("\n".join(lines))
        case "admin_logs":
            if message.from_user.id not in settings.bot.ADMINS:
                await message.answer("❌ Нет доступа")
                return
            metrics = await admin_metrics(db_session)
            await message.answer(
                "📊 Метрики:\n"
                f"Пользователей: {metrics['users']}\n"
                f"Подборок: {metrics['recommendations']}\n"
                f"Фото: {metrics['photos']}"

            )
        case "admin_catalog":
            if message.from_user.id not in settings.bot.ADMINS:
                await message.answer("❌ Нет доступа")
                return
            await message.answer("Управление каталогом пока в режиме заглушки.")


@router.callback_query(F.data == "style:start")
async def start_selection(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(StyleAssistantState.ASK_LOCATION)
    await callback.message.answer(
        "Отправь геолокацию, чтобы проверить погоду.",
        reply_markup=location_request_kb,
    )
    await callback.answer()

@router.callback_query(StyleAssistantState.ASK_LOCATION, F.data == "style:manual_city")
async def choose_manual_city(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(StyleAssistantState.ASK_CITY_MANUAL)
    await callback.message.answer(
        "Введите город текстом (например: Москва).",
        reply_markup=ReplyKeyboardRemove(),
    )
    await callback.answer()


@router.message(StyleAssistantState.ASK_LOCATION, F.location)
async def location_received(message: Message, state: FSMContext, user: User, db_session: AsyncSession) -> None:
    lat = message.location.latitude
    lon = message.location.longitude
    await upsert_location(
        db_session,
        user,
        city=None,
        lat=lat,
        lon=lon,
        allow_location=True,
    )
    await state.update_data(lat=lat, lon=lon, city=None)
    await state.set_state(StyleAssistantState.ASK_EVENT)
    await message.answer("Куда собираешься?", reply_markup=event_kb())

@router.message(StyleAssistantState.ASK_LOCATION)
async def location_not_received(message: Message, state: FSMContext) -> None:
    await state.set_state(StyleAssistantState.ASK_CITY_MANUAL)
    await message.answer(
        "Если не хотите отправлять геолокацию, введите город вручную.",
        reply_markup=ReplyKeyboardRemove(),
    )

@router.message(StyleAssistantState.ASK_CITY_MANUAL)
async def city_manual(message: Message, state: FSMContext, user: User, db_session: AsyncSession) -> None:
    city = (message.text or "").strip()
    if not city:
        await message.answer("Введите название города текстом.")
        return
    await upsert_location(db_session, user, city=city, lat=None, lon=None, allow_location=False)
    await state.update_data(city=city, lat=None, lon=None)
    await state.set_state(StyleAssistantState.ASK_EVENT)
    await message.answer("Куда собираешься?", reply_markup=event_kb())


@router.callback_query(StyleAssistantState.ASK_EVENT, F.data.startswith("style:event:"))
async def event_chosen(callback: CallbackQuery, state: FSMContext) -> None:
    event_type = callback.data.split(":", maxsplit=2)[2]
    await state.update_data(event_type=event_type)
    await state.set_state(StyleAssistantState.ASK_STYLE)
    await callback.message.answer("Выбери стиль", reply_markup=style_kb())
    await callback.answer()

@router.callback_query(StyleAssistantState.ASK_STYLE, F.data.startswith("style:style:"))
async def style_chosen(callback: CallbackQuery, state: FSMContext) -> None:
    style = callback.data.split(":", maxsplit=2)[2]
    await state.update_data(style=style)
    await state.set_state(StyleAssistantState.ASK_PHOTO_OPTIONAL)
    await callback.message.answer("Пришли фото (опционально) или пропусти.", reply_markup=photo_optional_kb())
    await callback.answer()

@router.callback_query(StyleAssistantState.ASK_PHOTO_OPTIONAL, F.data == "style:skip_photo")
async def skip_photo(callback: CallbackQuery, state: FSMContext, user: User, db_session: AsyncSession) -> None:
    await callback.answer()
    await _build_and_send_recommendations(callback.message, state, user, db_session)

@router.message(StyleAssistantState.ASK_PHOTO_OPTIONAL, F.photo)
async def photo_received(message: Message, state: FSMContext, user: User, db_session: AsyncSession) -> None:
    await save_photo(db_session, user, message.photo[-1].file_id)
    await message.answer("Фото сохранено. Анализ фото пока в режиме заглушки.")
    await _build_and_send_recommendations(message, state, user, db_session)

async def _build_and_send_recommendations(
    message: Message,
    state: FSMContext,
    user: User,
    db_session: AsyncSession,
) -> None:
    state_data = await state.get_data()
    event_type = state_data.get("event_type", "повседневно")
    style = state_data.get("style", "casual")
    city = state_data.get("city")
    lat = state_data.get("lat")
    lon = state_data.get("lon")

    weather = await generate_weather(city=city, lat=lat, lon=lon)
    pref = await save_preference(db_session, user, event_type=event_type, style=style)
    looks = build_recommendations(event_type, style, weather)

    weather_warning = f"\n⚠️ {weather.warning}" if weather.warning else ""
    text = (
            "Вот 3 варианта образа:\n"
            + "\n".join(looks)
            + f"\n\nПогода: {weather.summary}{weather_warning}"
    )
    await save_recommendation(db_session, user, pref, weather.summary, text)
    await state.set_state(StyleAssistantState.ASK_SHOPS)
    await message.answer(text)
    await message.answer("Показать магазины рядом?", reply_markup=shops_kb())


@router.callback_query(StyleAssistantState.ASK_SHOPS, F.data == "style:shops:yes")
async def shops_yes(callback: CallbackQuery, state: FSMContext, user: User, db_session: AsyncSession) -> None:
    history = await user_recommendation_history(db_session, user, limit=1)
    city = None
    if history:
        city = "рядом"
    shops = find_nearby_shops(city)
    await callback.message.answer("Магазины рядом:\n" + "\n".join(f"• {item}" for item in shops))
    await state.clear()
    await callback.answer()


@router.callback_query(StyleAssistantState.ASK_SHOPS, F.data == "style:shops:no")
async def shops_no(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.answer("Готово! Возвращайся за новым подбором через /start")
    await callback.answer()