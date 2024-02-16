#!/usr/bin/env python3

from dicebot.commands import web
from dicebot.test.utils import DicebotTestCase, TestMessageContext


class TestWeb(DicebotTestCase):
    async def test_web(self) -> None:
        # Arrange
        ctx = TestMessageContext.get()
        # Act
        await web.web(ctx)
        # Assert
        ctx.send.assert_awaited_once()
