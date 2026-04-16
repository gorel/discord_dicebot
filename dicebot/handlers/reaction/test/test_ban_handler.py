#!/usr/bin/env python3

import discord
from unittest.mock import AsyncMock, MagicMock, create_autospec, patch

from dicebot.data.db.active_event import ActiveEvent, EventType
from dicebot.handlers.reaction.ban_handler import BanReactionHandler
from dicebot.test.utils import DicebotTestCase, TestMessageContext


class TestBanReactionHandler(DicebotTestCase):
    @patch("dicebot.handlers.reaction.ban_handler.ActiveEvent.get_current", new_callable=AsyncMock)
    @patch("dicebot.handlers.reaction.ban_handler.ban", autospec=True)
    async def test_should_handle_turbo_day_threshold_one(self, mock_ban, mock_get_current):
        """TURBO_DAY: should_handle returns True when reaction.count == 1"""
        ctx = TestMessageContext.get(reaction=create_autospec(discord.Reaction))
        ctx.reaction.count = 1
        ctx.reaction.message.author.id = 999
        ctx.client.user.id = 1

        mock_event = MagicMock(spec=ActiveEvent)
        mock_event.event_type_enum = EventType.TURBO_DAY
        mock_get_current.return_value = mock_event

        handler = BanReactionHandler()
        with patch.object(handler, "should_handle_without_threshold_check", new_callable=AsyncMock, return_value=True):
            result = await handler.should_handle(ctx)

        self.assertTrue(result)

    @patch("dicebot.handlers.reaction.ban_handler.ActiveEvent.get_current", new_callable=AsyncMock)
    @patch("dicebot.handlers.reaction.ban_handler.ban", autospec=True)
    async def test_should_handle_turbo_day_threshold_not_met(self, mock_ban, mock_get_current):
        """TURBO_DAY: should_handle returns False when reaction.count != 1"""
        ctx = TestMessageContext.get(reaction=create_autospec(discord.Reaction))
        ctx.reaction.count = 3
        ctx.reaction.message.author.id = 999
        ctx.client.user.id = 1

        mock_event = MagicMock(spec=ActiveEvent)
        mock_event.event_type_enum = EventType.TURBO_DAY
        mock_get_current.return_value = mock_event

        handler = BanReactionHandler()
        with patch.object(handler, "should_handle_without_threshold_check", new_callable=AsyncMock, return_value=True):
            result = await handler.should_handle(ctx)

        self.assertFalse(result)
