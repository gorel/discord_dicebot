#!/usr/bin/env python3

from dicebot.handlers.message.quotes_only_handler import (
    QUOTES_ONLY_IMAGE_URL,
    QuotesOnlyHandler,
)
from dicebot.test.utils import DicebotTestCase, TestMessageContext


def _ctx(content: str, channel_name: str = "quotes-only") -> TestMessageContext:
    ctx = TestMessageContext.get(content)
    ctx.message.channel.name = channel_name
    return ctx


class TestQuotesOnlyHandler(DicebotTestCase):
    async def test_should_handle_message_without_quotes(self):
        handler = QuotesOnlyHandler()
        self.assertTrue(await handler.should_handle(_ctx("lol that's funny")))

    async def test_should_handle_message_with_single_quote(self):
        handler = QuotesOnlyHandler()
        self.assertTrue(await handler.should_handle(_ctx('he said "hi')))

    async def test_should_not_handle_message_with_quote_pair(self):
        handler = QuotesOnlyHandler()
        self.assertFalse(await handler.should_handle(_ctx('"hello there" - Obi-Wan')))

    async def test_should_not_handle_message_with_smart_quotes(self):
        handler = QuotesOnlyHandler()
        self.assertFalse(await handler.should_handle(_ctx("“hello there” - Obi-Wan")))

    async def test_should_not_handle_other_channels(self):
        handler = QuotesOnlyHandler()
        self.assertFalse(await handler.should_handle(_ctx("no quotes", "general")))

    async def test_handle_replies_with_image(self):
        ctx = _ctx("no quotes")
        await QuotesOnlyHandler().handle(ctx)
        ctx.quote_reply.assert_awaited_once_with(QUOTES_ONLY_IMAGE_URL)
