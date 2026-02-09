from types import SimpleNamespace

import pytest

from bot.handlers import command as command_module
from bot.internal.enums import StyleAssistantState


class FakeMessage:
    def __init__(self) -> None:
        self.answers: list[str] = []
        self.from_user = SimpleNamespace(id=1)


    async def answer(self, text: str, *args, **kwargs) -> None:
        self.answers.append(text)




class FakeState:
    def __init__(self) -> None:
        self.state = None

    async def set_state(self, state) -> None:
        self.state = state


@pytest.mark.anyio
async def test_start_sets_onboarding_state() -> None:
    message = FakeMessage()
    state = FakeState()


    await command_module.command_handler(
        message=message,
        command=SimpleNamespace(command="start"),
        user=SimpleNamespace(),
        settings=SimpleNamespace(bot=SimpleNamespace(ADMINS=[])),
        state=state,
        db_session=SimpleNamespace(),
    )
    assert state.state == StyleAssistantState.ONBOARDING_START
    assert message.answers
    assert "Style Assistant Bot" in message.answers[0]