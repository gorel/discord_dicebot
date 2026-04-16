#!/usr/bin/env python3

import discord
from sqlalchemy.exc import IntegrityError
from unittest.mock import AsyncMock, MagicMock, create_autospec, patch

from dicebot.data.db.scheduled_event import ScheduledEvent, ScheduledEventSignup
from dicebot.handlers.reaction.eyes_handler import EyesReactionHandler
from dicebot.test.utils import DicebotTestCase, TestMessageContext


class TestEyesReactionHandler(DicebotTestCase):
    @patch("dicebot.handlers.reaction.eyes_handler.ScheduledEvent.get_by_message_id", new_callable=AsyncMock)
    async def test_should_handle_non_eyes_emoji(self, mock_get):
        ctx = TestMessageContext.get(reaction=create_autospec(discord.Reaction))
        # Use a non-eyes custom emoji name
        ctx.reaction.emoji = MagicMock(name="thumbsup")
        ctx.reaction.emoji.name = "thumbsup"
        handler = EyesReactionHandler()
        result = await handler.should_handle(ctx)
        self.assertFalse(result)
        mock_get.assert_not_called()

    @patch("dicebot.handlers.reaction.eyes_handler.ScheduledEvent.get_by_message_id", new_callable=AsyncMock)
    async def test_should_handle_no_matching_event(self, mock_get):
        ctx = TestMessageContext.get(reaction=create_autospec(discord.Reaction))
        ctx.reaction.emoji = MagicMock()
        ctx.reaction.emoji.name = "eyes"
        mock_get.return_value = None
        handler = EyesReactionHandler()
        result = await handler.should_handle(ctx)
        self.assertFalse(result)

    @patch("dicebot.handlers.reaction.eyes_handler.ScheduledEvent.get_by_message_id", new_callable=AsyncMock)
    async def test_should_handle_matching_event(self, mock_get):
        ctx = TestMessageContext.get(reaction=create_autospec(discord.Reaction))
        ctx.reaction.emoji = MagicMock()
        ctx.reaction.emoji.name = "eyes"
        mock_get.return_value = MagicMock(spec=ScheduledEvent, id=1)
        handler = EyesReactionHandler()
        result = await handler.should_handle(ctx)
        self.assertTrue(result)

    @patch("dicebot.handlers.reaction.eyes_handler.ScheduledEvent.get_by_message_id", new_callable=AsyncMock)
    async def test_handle_creates_signup(self, mock_get):
        ctx = TestMessageContext.get(reaction=create_autospec(discord.Reaction))
        ctx.reactor.id = 42
        mock_event = MagicMock(spec=ScheduledEvent, id=1)
        mock_get.return_value = mock_event
        handler = EyesReactionHandler()
        handler._cached_event = mock_event
        await handler.handle(ctx)
        ctx.session.add.assert_called_once()
        ctx.session.commit.assert_awaited_once()

    @patch("dicebot.handlers.reaction.eyes_handler.ScheduledEvent.get_by_message_id", new_callable=AsyncMock)
    async def test_handle_duplicate_signup_no_error(self, mock_get):
        ctx = TestMessageContext.get(reaction=create_autospec(discord.Reaction))
        ctx.reactor.id = 42
        mock_event = MagicMock(spec=ScheduledEvent, id=1)
        mock_get.return_value = mock_event
        ctx.session.commit = AsyncMock(side_effect=IntegrityError("", {}, Exception()))
        handler = EyesReactionHandler()
        handler._cached_event = mock_event
        # Should not raise
        await handler.handle(ctx)
        ctx.session.rollback.assert_awaited_once()

    async def test_record_handled_is_noop(self):
        ctx = TestMessageContext.get(reaction=create_autospec(discord.Reaction))
        handler = EyesReactionHandler()
        await handler.record_handled(ctx)
        ctx.session.add.assert_not_called()
        ctx.session.commit.assert_not_awaited()

    @patch("dicebot.handlers.reaction.eyes_handler.ScheduledEvent.get_by_message_id", new_callable=AsyncMock)
    async def test_handle_event_none(self, mock_get):
        ctx = TestMessageContext.get(reaction=create_autospec(discord.Reaction))
        ctx.reactor.id = 42
        mock_get.return_value = None
        handler = EyesReactionHandler()
        handler._cached_event = None  # simulate should_handle setting cache to None
        await handler.handle(ctx)
        ctx.session.add.assert_not_called()
