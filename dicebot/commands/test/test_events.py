#!/usr/bin/env python3

from unittest.mock import AsyncMock, MagicMock, patch

from dicebot.commands import events
from dicebot.data.db.active_event import ActiveEvent, EventType
from dicebot.test.utils import DicebotTestCase, TestMessageContext


class TestEventsOn(DicebotTestCase):
    async def test_events_on_valid(self) -> None:
        # Arrange
        ctx = TestMessageContext.get()
        ctx.author.is_admin_of.return_value = True
        # Act
        await events.events_on(ctx, 0.25)
        # Assert
        self.assertEqual(0.25, ctx.guild.events_probability)
        self.assertEqual(ctx.channel.id, ctx.guild.events_channel_id)
        ctx.session.commit.assert_awaited_once()
        ctx.channel.send.assert_awaited_once()

    async def test_events_on_invalid_probability_zero(self) -> None:
        # Arrange
        ctx = TestMessageContext.get()
        ctx.author.is_admin_of.return_value = True
        # Act
        await events.events_on(ctx, 0)
        # Assert
        ctx.channel.send.assert_awaited_once()
        ctx.session.commit.assert_not_awaited()

    async def test_events_on_invalid_probability_over_one(self) -> None:
        # Arrange
        ctx = TestMessageContext.get()
        ctx.author.is_admin_of.return_value = True
        # Act
        await events.events_on(ctx, 1.5)
        # Assert
        ctx.channel.send.assert_awaited_once()
        ctx.session.commit.assert_not_awaited()


class TestEventsOff(DicebotTestCase):
    async def test_events_off(self) -> None:
        # Arrange
        ctx = TestMessageContext.get()
        ctx.author.is_admin_of.return_value = True
        ctx.guild.events_probability = 0.25
        # Act
        await events.events_off(ctx)
        # Assert
        self.assertIsNone(ctx.guild.events_probability)
        ctx.session.commit.assert_awaited_once()
        ctx.channel.send.assert_awaited_once()


class TestEventsStatus(DicebotTestCase):
    async def test_events_status_disabled(self) -> None:
        # Arrange
        ctx = TestMessageContext.get()
        ctx.guild.events_probability = None
        # Act
        await events.events_status(ctx)
        # Assert
        ctx.channel.send.assert_awaited_once()
        call_args = ctx.channel.send.call_args[0][0]
        self.assertIn("disabled", call_args)

    @patch(
        "dicebot.commands.events.ActiveEvent.get_current",
        new_callable=AsyncMock,
    )
    @patch("dicebot.commands.events.timezone")
    async def test_events_status_no_active_event(
        self, mock_timezone, mock_get_current
    ) -> None:
        # Arrange
        ctx = TestMessageContext.get()
        ctx.guild.events_probability = 0.25
        mock_get_current.return_value = None
        # Act
        await events.events_status(ctx)
        # Assert
        ctx.channel.send.assert_awaited_once()
        call_args = ctx.channel.send.call_args[0][0]
        self.assertIn("25%", call_args)
        self.assertIn("No event active today", call_args)

    @patch(
        "dicebot.commands.events.ActiveEvent.get_current",
        new_callable=AsyncMock,
    )
    @patch("dicebot.commands.events.timezone")
    async def test_events_status_active_event(
        self, mock_timezone, mock_get_current
    ) -> None:
        # Arrange
        ctx = TestMessageContext.get()
        ctx.guild.events_probability = 0.25
        mock_timezone.localize_dt.return_value = "tomorrow at 12:00 AM PST"

        active = MagicMock(spec=ActiveEvent)
        active.event_type_enum = EventType.LUCKY_HOUR
        active.expires_at = MagicMock()
        mock_get_current.return_value = active
        # Act
        await events.events_status(ctx)
        # Assert
        ctx.channel.send.assert_awaited_once()
        call_args = ctx.channel.send.call_args[0][0]
        self.assertIn("25%", call_args)
        self.assertIn("Lucky Hour", call_args)
        self.assertIn("tomorrow at 12:00 AM PST", call_args)
