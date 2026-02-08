import functools
import logging
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        try:
            name = self._get_name(handler)
            logger.info(f"calling {name}")
        finally:
            res = await handler(event, data)
            return res

    def _get_name(self, handler):
        while isinstance(handler, functools.partial):
            handler = handler.args[0]

        name = handler.__wrapped__.__self__.callback.__name__
        return name
