from aiogram.types import InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def start_selection_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="Начать подбор", callback_data="style:start")
    return kb.as_markup()


def event_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="Повседневно", callback_data="style:event:повседневно")
    kb.button(text="Мероприятие", callback_data="style:event:мероприятие")
    kb.adjust(1)
    return kb.as_markup()


def style_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="Casual", callback_data="style:style:casual")
    kb.button(text="Classic", callback_data="style:style:classic")
    kb.button(text="Sport", callback_data="style:style:sport")
    kb.adjust(1)
    return kb.as_markup()


def photo_optional_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="Пропустить фото", callback_data="style:skip_photo")
    return kb.as_markup()


def shops_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="Да, показать магазины", callback_data="style:shops:yes")
    kb.button(text="Нет, спасибо", callback_data="style:shops:no")
    kb.adjust(1)
    return kb.as_markup()

location_request_kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📍 Отправить геолокацию", request_location=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )