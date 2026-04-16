#!/usr/bin/env python3

from unittest.mock import AsyncMock, patch

from dicebot.commands import roast
from dicebot.test.utils import DicebotTestCase, TestMessageContext


class TestRoast(DicebotTestCase):
    @patch("dicebot.commands.roast.AskOpenAI")
    async def test_generate_roast_calls_ai(self, mock_ask_cls):
        # Arrange
        ctx = TestMessageContext.get()
        ctx.message.author.name = "TestUser"
        mock_asker = AsyncMock()
        mock_asker.ask = AsyncMock(return_value="You're terrible!")
        mock_ask_cls.return_value = mock_asker
        # Act
        await roast.generate_roast(ctx, roll=1, die_size=10)
        # Assert
        mock_asker.ask.assert_awaited_once()
        call_args = mock_asker.ask.call_args
        prompt = call_args.args[0]
        assert "TestUser" in prompt
        assert "1" in prompt
        assert "d10" in prompt or "10" in prompt

    @patch("dicebot.commands.roast.AskOpenAI")
    async def test_generate_roast_sends_response(self, mock_ask_cls):
        # Arrange
        ctx = TestMessageContext.get()
        ctx.message.author.name = "TestUser"
        mock_asker = AsyncMock()
        mock_asker.ask = AsyncMock(return_value="You absolute disaster!")
        mock_ask_cls.return_value = mock_asker
        # Act
        await roast.generate_roast(ctx, roll=1, die_size=6)
        # Assert
        ctx.channel.send.assert_awaited_once_with("You absolute disaster!", silent=True)

    @patch("dicebot.commands.roast.AskOpenAI")
    async def test_generate_roast_swallows_errors(self, mock_ask_cls):
        # Arrange
        ctx = TestMessageContext.get()
        mock_asker = AsyncMock()
        mock_asker.ask = AsyncMock(side_effect=Exception("API down"))
        mock_ask_cls.return_value = mock_asker
        # Act - should not raise
        await roast.generate_roast(ctx, roll=1, die_size=6)
        # Assert - ctx.send never called
        ctx.channel.send.assert_not_awaited()
