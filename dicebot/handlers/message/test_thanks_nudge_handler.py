#!/usr/bin/env python3

from unittest.mock import AsyncMock

from dicebot.handlers.message.thanks_nudge_handler import ThanksNudgeHandler
from dicebot.test.utils import TestMessageContext, DicebotTestCase


class TestThanksNudgeHandler(DicebotTestCase):
    async def test_should_handle_when_thanks_present(self):
        ctx = TestMessageContext.get("Thanks for your help!")
        handler = ThanksNudgeHandler()
        self.assertTrue(await handler.should_handle(ctx))

    async def test_should_not_handle_for_commands(self):
        ctx = TestMessageContext.get("!thanks @user Great job")
        handler = ThanksNudgeHandler()
        self.assertFalse(await handler.should_handle(ctx))

    async def test_should_not_handle_if_no_thanks(self):
        ctx = TestMessageContext.get("hello world")
        handler = ThanksNudgeHandler()
        self.assertFalse(await handler.should_handle(ctx))

    async def test_handle_sends_nudge(self):
        ctx = TestMessageContext.get("thanks bot")
        ctx.send = AsyncMock()
        handler = ThanksNudgeHandler()
        await handler.handle(ctx)
        expected = f"{ctx.author.as_mention()} Please use `!thanks` to publicly record your thanks!"
        ctx.send.assert_called_once_with(expected)