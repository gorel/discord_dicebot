#!/usr/bin/env python3

import discord
from unittest.mock import AsyncMock, MagicMock, create_autospec, patch

from dicebot.data.db.scheduled_event import ScheduledEvent, ScheduledEventSignup
from dicebot.handlers.reaction.eyes_handler import EyesReactionHandler
from dicebot.test.utils import DicebotTestCase, TestMessageContext


class TestEyesReactionHandler(DicebotTestCase):
    @patch("dicebot.handlers.reaction.eyes_handler.ScheduledEvent.get_by_message_id", new_callable=AsyncMock)
    async def test_should_handle_non_eyes_emoji(self, mock_get):
        ctx = TestMessageContext.get(reaction=create_autospec(discord.Reaction))
        # Make is_emoji_with_name return False
        handler = EyesReactionHandler()
        with patch.object(handler, "is_emoji_with_name", return_value=False):
            result = await handler.should_handle(ctx)
        self.assertFalse(result)
        mock_get.assert_not_called()

    @patch("dicebot.handlers.reaction.eyes_handler.ScheduledEvent.get_by_message_id", new_callable=AsyncMock)
    async def test_should_handle_no_matching_event(self, mock_get):
        ctx = TestMessageContext.get(reaction=create_autospec(discord.Reaction))
        mock_get.return_value = None
        handler = EyesReactionHandler()
        with patch.object(handler, "is_emoji_with_name", return_value=True):
            result = await handler.should_handle(ctx)
        self.assertFalse(result)

    @patch("dicebot.handlers.reaction.eyes_handler.ScheduledEvent.get_by_message_id", new_callable=AsyncMock)
    async def test_should_handle_matching_event(self, mock_get):
        ctx = TestMessageContext.get(reaction=create_autospec(discord.Reaction))
        mock_get.return_value = MagicMock(spec=ScheduledEvent, id=1)
        handler = EyesReactionHandler()
        with patch.object(handler, "is_emoji_with_name", return_value=True):
            result = await handler.should_handle(ctx)
        self.assertTrue(result)

    @patch("dicebot.handlers.reaction.eyes_handler.ScheduledEvent.get_by_message_id", new_callable=AsyncMock)
    async def test_handle_creates_signup(self, mock_get):
        ctx = TestMessageContext.get(reaction=create_autospec(discord.Reaction))
        ctx.reactor.id = 42
        mock_event = MagicMock(spec=ScheduledEvent, id=1)
        mock_get.return_value = mock_event
        handler = EyesReactionHandler()
        await handler.handle(ctx)
        ctx.session.add.assert_called_once()
        ctx.session.commit.assert_awaited_once()

    @patch("dicebot.handlers.reaction.eyes_handler.ScheduledEvent.get_by_message_id", new_callable=AsyncMock)
    async def test_handle_duplicate_signup_no_error(self, mock_get):
        from sqlalchemy.exc import IntegrityError
        ctx = TestMessageContext.get(reaction=create_autospec(discord.Reaction))
        ctx.reactor.id = 42
        mock_event = MagicMock(spec=ScheduledEvent, id=1)
        mock_get.return_value = mock_event
        ctx.session.commit = AsyncMock(side_effect=IntegrityError("", {}, Exception()))
        handler = EyesReactionHandler()
        # Should not raise
        await handler.handle(ctx)
        ctx.session.rollback.assert_awaited_once()
