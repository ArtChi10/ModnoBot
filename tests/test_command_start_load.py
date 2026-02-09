import asyncio
from types import SimpleNamespace

import pytest

from bot.handlers import command as command_module
from bot.internal.enums import StyleAssistantState


class FakeMessage:
    def __init__(self, user_id: int) -> None:
        self.answers: list[str] = []
        self.from_user = SimpleNamespace(id=user_id)

    async def answer(self, text: str, *args, **kwargs) -> None:
        self.answers.append(text)


class FakeState:
    def __init__(self) -> None:
        self.state = None

    async def set_state(self, state) -> None:
        self.state = state


@pytest.mark.asyncio
async def test_command_start_under_load():
    async def run_once(user_id: int):
        message = FakeMessage(user_id)

        await command_module.command_handler(
            message=message,
            command=SimpleNamespace(command="start"),
            user=SimpleNamespace(),
            settings=SimpleNamespace(bot=SimpleNamespace(ADMINS=[])),
            state=state,
            db_session=SimpleNamespace(),
        )

        return state.state, message.answers
    for i in range(100):
        state, answers = await run_once(i)
        assert state == StyleAssistantState.ONBOARDING_START
        assert answers
        assert "Style Assistant Bot" in answers[0]
    results = await asyncio.gather(*[run_once(i) for i in range(50)])
    for state, answers in results:
        assert state == StyleAssistantState.ONBOARDING_START
        assert answers
        assert "Style Assistant Bot" in answers[0]
