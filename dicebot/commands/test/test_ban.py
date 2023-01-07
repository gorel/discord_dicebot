#!/usr/bin/env python3

import asyncio
import datetime
import unittest
from unittest.mock import create_autospec, patch

from dicebot.commands import ban
from dicebot.data.db.ban import Ban
from dicebot.data.db.user import User
from dicebot.data.types.time import Time
from dicebot.test.utils import TestMessageContext


class TestBan(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        await super().asyncSetUp()
        asyncio.get_running_loop().set_debug(False)

    @patch("dicebot.commands.ban.unban_task", autospec=True)
    @patch("dicebot.commands.ban.Ban.get_latest_unvoided_ban", autospec=True)
    async def test_ban_internal(self, mock_ban, mock_unban_task) -> None:
        with self.subTest("simple"):
            # Arrange
            ctx = TestMessageContext.get()
            target = create_autospec(User)
            timer = create_autospec(Time)
            mock_ban.return_value = None
            # Act
            with patch("dicebot.commands.ban.timezone"):
                await ban.ban_internal(ctx, target, timer, False, "ban reason")
            # Assert
            ctx.session.refresh.assert_awaited_once()
            mock_unban_task.apply_async.assert_called_once()

    @patch("dicebot.commands.ban.unban_task", autospec=True)
    @patch("dicebot.commands.ban.Ban.get_latest_unvoided_ban", autospec=True)
    async def test_ban_internal_already_banned(self, mock_ban, mock_unban_task) -> None:
        with self.subTest("already banned"):
            # Arrange
            ctx = TestMessageContext.get()
            target = create_autospec(User)
            timer = create_autospec(Time, seconds=30)
            until = datetime.datetime.now() + datetime.timedelta(days=7)
            mock_ban.return_value = create_autospec(Ban, banned_until=until)
            # Act
            with patch("dicebot.commands.ban.timezone"):
                await ban.ban_internal(ctx, target, timer, False, "ban reason")
            # Assert
            ctx.session.refresh.assert_not_awaited()
            mock_unban_task.apply_async.assert_not_called()

    @patch("dicebot.commands.ban.ban_internal", autospec=True)
    async def test_ban(self, mock_ban_internal) -> None:
        # Arrange
        ctx = TestMessageContext.get()
        target = create_autospec(User)
        timer = create_autospec(Time)
        # Act
        await ban.ban(ctx, target, timer)
        # Assert
        mock_ban_internal.assert_awaited_once()

    async def test_unban_internal(self) -> None:
        # Arrange
        ctx = TestMessageContext.get()
        target = create_autospec(User)
        # Act
        await ban.unban_internal(ctx, target, "msg")
        # Assert
        ctx.guild.unban.assert_awaited_once()
        ctx.session.commit.assert_awaited_once()
        ctx.channel.send.assert_awaited_once()

    @patch("dicebot.commands.ban.unban_internal", autospec=True)
    async def test_unban(self, mock_unban_internal) -> None:
        # Arrange
        ctx = TestMessageContext.get()
        target = create_autospec(User)
        # Act
        await ban.unban(ctx, target)
        # Assert
        mock_unban_internal.assert_awaited_once()

    async def test_ban_leaderboard(self) -> None:
        # Arrange
        ctx = TestMessageContext.get()
        # Act
        await ban.ban_leaderboard(ctx)
        # Assert
        ctx.guild.ban_scoreboard_str.assert_awaited_once()
        ctx.channel.send.assert_awaited_once()

    @patch("dicebot.commands.ban.ban_internal", autospec=True)
    async def test_turboban(self, mock_ban_internal) -> None:
        # Arrange
        ctx = TestMessageContext.get()
        target = create_autospec(User)
        # Act
        await ban.turboban(ctx, target)
        # Assert
        ctx.quote_reply.assert_awaited_once()
        mock_ban_internal.assert_awaited_once()
