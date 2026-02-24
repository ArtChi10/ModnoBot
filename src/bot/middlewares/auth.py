import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message

from asyncpg.exceptions import UniqueViolationError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from bot.controllers.user import add_user_to_db, get_user_from_db_by_tg_id
from database.models import User as BotUser

logger = logging.getLogger(__name__)
class AuthMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Any, dict[str, Any]], Awaitable[Any]],
        event: Any,
        data: dict[str, Any],
    ) -> Any:
        db_session: AsyncSession = data["db_session"]
        user = await self._resolve_user(event, db_session)
        data["is_new_user"] = data.get("is_new_user", False)
        data["user"] = user
        return await handler(event, data)

    async def _resolve_user(self, event: Any, db_session: AsyncSession) -> BotUser:
        tg_id = event.from_user.id

        for attempt in range(3):
            user = await get_user_from_db_by_tg_id(tg_id, db_session)
            if user:
                return user

            source = self._extract_start_source(event)
            try:
                user = await add_user_to_db(event.from_user, db_session, source)
                if user:
                    return user
            except (UniqueViolationError, IntegrityError):
                await db_session.rollback()
                logger.info("Retrying user creation for tg_id=%s (attempt=%s)", tg_id, attempt + 1)
                await asyncio.sleep(0)

            logger.error("Unable to resolve user after retries for tg_id=%s", tg_id)
            raise RuntimeError(f"Unable to resolve user for tg_id={tg_id}")

        @staticmethod
        def _extract_start_source(event: Any) -> str | None:
            if isinstance(event, Message) and event.text and event.text.startswith("/start"):
                parts = event.text.split(maxsplit=1)
                if len(parts) == 2:
                    return parts[1].strip()
            return None