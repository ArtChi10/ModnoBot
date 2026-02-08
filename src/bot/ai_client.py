import logging
from asyncio import get_running_loop, sleep

from aiogram.types import Message
from openai import AsyncOpenAI, BadRequestError
from openai.types.beta.threads import (
    ImageFileContentBlockParam,
    ImageURLContentBlockParam,
    TextContentBlockParam,
)
from sqlalchemy.ext.asyncio import AsyncSession

from bot.internal.lexicon import replies
from database.models import User

logger = logging.getLogger(__name__)

ContentType = str | list[TextContentBlockParam | ImageFileContentBlockParam | ImageURLContentBlockParam]


class AIClient:
    def __init__(self, token: str, assistant_id: str):
        self.client = AsyncOpenAI(api_key=token)
        self.assistant_id = assistant_id

    async def delete_thread(self, thread_id: str):
        await self.client.beta.threads.delete(thread_id)

    async def new_thread(self) -> str:
        thread = await self.client.beta.threads.create()
        logging.debug(f"Created new thread {thread.id}")
        return thread.id

    async def _ensure_thread_available(self, thread_id: str, message: Message, fullname: str):
        while True:
            runs = await self.client.beta.threads.runs.list(thread_id=thread_id, limit=1)
            if runs.data and runs.data[0].status in ("queued", "in_progress"):
                logger.info(f"Active run detected {runs.data[0].id} in thread {thread_id}")
                await message.answer(replies[2].format(fullname=fullname))
                await sleep(2)
            else:
                break

    async def _safe_create_message(
        self,
        thread_id: str,
        content: ContentType,
        message: Message,
        fullname: str,
        retry: int = 0,
        max_retries: int = 3,
    ) -> bool:
        try:
            await self.client.beta.threads.messages.create(
                thread_id=thread_id,
                role="user",
                content=content,
            )
        except BadRequestError as e:
            if "while a run" in str(e):
                logger.warning(f"Race condition: run started after check (retry={retry})")
                if retry >= max_retries:
                    await message.answer("Произошла ошибка: ассистент сейчас занят, попробуйте позже.")
                    return False
                await sleep(2)
                return await self._safe_create_message(thread_id, content, message, fullname, retry + 1, max_retries)
            raise
        return True

    async def _run_thread_and_get_response(self, thread_id: str) -> str | None:
        run = await self.client.beta.threads.runs.create(thread_id=thread_id, assistant_id=self.assistant_id)
        run = await self.wait_for_run_completion(thread_id, run.id)

        if run.status == "completed":
            messages = await self.client.beta.threads.messages.list(thread_id=thread_id)
            response = messages.data[0].content[0].text.value
            logger.debug(f"Thread {thread_id} responded with: {response[:100]}...")
            return response
        return None

    async def get_response(
        self,
        ai_thread_id: str,
        text: str,
        message: Message,
        fullname: str,
        retry: int = 0,
        max_retries: int = 3,
    ) -> str | None:
        await self._ensure_thread_available(ai_thread_id, message, fullname)

        success = await self._safe_create_message(ai_thread_id, text, message, fullname, retry, max_retries)
        if not success:
            return None

        return await self._run_thread_and_get_response(ai_thread_id)

    async def get_response_with_image(
        self,
        thread_id: str,
        text: str,
        image_bytes: bytes,
        message: Message,
        fullname: str,
        retry: int = 0,
        max_retries: int = 3,
    ) -> str | None:
        try:
            await self._ensure_thread_available(thread_id, message, fullname)

            uploaded_file = await self.client.files.create(
                file=("image.png", image_bytes, "image/png"),
                purpose="assistants",
            )

            content = [
                TextContentBlockParam(type="text", text=text),
                ImageFileContentBlockParam(type="image_file", image_file={"file_id": uploaded_file.id}),
            ]

            success = await self._safe_create_message(thread_id, content, message, fullname, retry, max_retries)
            if not success:
                return None

            return await self._run_thread_and_get_response(thread_id)

        except BadRequestError as e:
            logger.exception(f"OpenAI API Error: {e}")
            if e.status_code == 429:
                return "Превышены лимиты запросов. Пожалуйста, попробуйте позже."
            return "Ошибка при обработке изображения. Убедитесь, что файл корректного формата."

    async def apply_context_to_thread(
        self,
        user: User,
        context: str,
        db_session: AsyncSession,
        use_existing_thread: bool = False,
    ) -> str:
        if use_existing_thread and user.ai_thread:
            thread_id = user.ai_thread
            await self.client.beta.threads.messages.create(thread_id=thread_id, role="user", content=context)
        else:
            thread = await self.client.beta.threads.create()
            thread_id = thread.id
            await self.client.beta.threads.messages.create(thread_id=thread_id, role="user", content=context)
            user.ai_thread = thread_id

        user.is_context_added = True
        db_session.add(user)
        await db_session.flush()
        logger.info(f"Added context to thread {thread_id}")
        return thread_id

    async def wait_for_run_completion(self, thread_id: str, run_id: str, interval: int = 2, timeout: int = 120):
        start = get_running_loop().time()
        while True:
            run = await self.client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_id)
            if run.status in ("completed", "failed", "cancelled", "expired"):
                return run
            if get_running_loop().time() - start > timeout:
                raise TimeoutError(f"Run {run_id} in thread {thread_id} did not finish in time")
            await sleep(interval)
