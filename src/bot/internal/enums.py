from enum import StrEnum, auto

from aiogram.fsm.state import State, StatesGroup


class Form(StatesGroup):
    space = State()
    geography = State()
    request = State()


class AIState(StatesGroup):
    IN_AI_DIALOG = State()
    WAITING_HOME_TIME = State()
    WAITING_CONFIRM_HOME = State()
    WAITING_PLANT_PHOTO = State()
    WAITING_CITY = State()


class StyleAssistantState(StatesGroup):
    ONBOARDING_START = State()
    ASK_LOCATION = State()
    ASK_CITY_MANUAL = State()
    ASK_EVENT = State()
    ASK_STYLE = State()
    ASK_PHOTO_OPTIONAL = State()
    ASK_SHOPS = State()


class Stage(StrEnum):
    DEV = auto()
    PROD = auto()
