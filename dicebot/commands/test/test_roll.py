#!/usr/bin/env python3

import asyncio
import datetime
import unittest
from unittest.mock import AsyncMock, create_autospec, patch

from dicebot.commands import roll
from dicebot.data.db.roll import Roll
from dicebot.data.types.greedy_str import GreedyStr
from dicebot.test.utils import TestMessageContext


class TestRoll(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        await super().asyncSetUp()
        asyncio.get_running_loop().set_debug(False)

    @patch("dicebot.commands.roll.Roll", autospec=True)
    @patch("dicebot.commands.roll.ban", autospec=True)
    async def test_roll_no_gambling(self, mock_ban, mock_roll) -> None:
        with self.subTest("simple"):
            # Arrange
            ctx = TestMessageContext.get()
            ctx.guild.timezone = "US/Pacific"
            ctx.guild.roll_timeout = 0
            ctx.guild.current_roll = 333
            ctx.guild.gambling_limit = None
            mock_last_roll = create_autospec(Roll, rolled_at=datetime.datetime.now())
            mock_roll.get_last_roll = AsyncMock(return_value=mock_last_roll)
            # Act
            with patch("dicebot.commands.roll.random") as mock_random:
                mock_random.randint.return_value = 123
                await roll.roll(ctx, GreedyStr(""))
            # Assert
            mock_roll.assert_called_once()
            mock_ban.ban_internal.assert_not_awaited()
            ctx.session.commit.assert_awaited_once()
            ctx.channel.send.assert_awaited()
        with self.subTest("first roll ever"):
            # Arrange
            mock_roll.reset_mock()
            mock_ban.reset_mock()
            ctx = TestMessageContext.get()
            ctx.guild.roll_timeout = 0
            ctx.guild.current_roll = 333
            ctx.guild.gambling_limit = None
            mock_roll.get_last_roll = AsyncMock(return_value=None)
            # Act
            with patch("dicebot.commands.roll.random") as mock_random:
                mock_random.randint.return_value = 123
                await roll.roll(ctx, GreedyStr(""))
            # Assert
            mock_roll.assert_called_once()
            mock_ban.ban_internal.assert_not_awaited()
            ctx.session.commit.assert_awaited_once()
            ctx.channel.send.assert_awaited()
        with self.subTest("rolled recently"):
            # Arrange
            mock_roll.reset_mock()
            mock_ban.reset_mock()
            ctx = TestMessageContext.get()
            ctx.guild.timezone = "US/Pacific"
            ctx.guild.roll_timeout = 1
            ctx.guild.current_roll = 333
            ctx.guild.gambling_limit = None
            mock_last_roll = create_autospec(Roll, rolled_at=datetime.datetime.now())
            mock_roll.get_last_roll = AsyncMock(return_value=mock_last_roll)
            # Act
            with patch("dicebot.commands.roll.random") as mock_random:
                mock_random.randint.return_value = 123
                await roll.roll(ctx, GreedyStr(""))
            # Assert
            mock_roll.assert_not_called()
            mock_ban.ban_internal.assert_awaited_once()
            ctx.session.commit.assert_not_awaited()
            ctx.channel.send.assert_awaited_once()
        with self.subTest("rolled 1"):
            # Arrange
            mock_roll.reset_mock()
            mock_ban.reset_mock()
            ctx = TestMessageContext.get()
            ctx.guild.roll_timeout = 0
            ctx.guild.current_roll = 333
            ctx.guild.gambling_limit = None
            mock_roll.get_last_roll = AsyncMock(return_value=None)
            # Act
            with patch("dicebot.commands.roll.random") as mock_random:
                mock_random.randint.return_value = 1
                await roll.roll(ctx, GreedyStr(""))
            # Assert
            mock_roll.assert_called_once()
            mock_ban.ban_internal.assert_awaited_once()
            ctx.session.commit.assert_awaited_once()
            ctx.channel.send.assert_awaited()
        with self.subTest("rolled one off"):
            # Arrange
            mock_roll.reset_mock()
            mock_ban.reset_mock()
            ctx = TestMessageContext.get()
            ctx.guild.roll_timeout = 0
            ctx.guild.current_roll = 333
            ctx.guild.allow_renaming = True
            ctx.guild.gambling_limit = None
            mock_roll.get_last_roll = AsyncMock(return_value=None)
            # Act
            with patch("dicebot.commands.roll.random") as mock_random:
                mock_random.randint.return_value = 332
                await roll.roll(ctx, GreedyStr(""))
            # Assert
            mock_roll.assert_called_once()
            mock_ban.ban_internal.assert_not_awaited()
            ctx.session.commit.assert_awaited()
            ctx.channel.send.assert_awaited()
            ctx.guild.add_chat_rename.assert_awaited_once()
            ctx.guild.add_guild_rename.assert_not_awaited()
        with self.subTest("rolled win"):
            # Arrange
            mock_roll.reset_mock()
            mock_ban.reset_mock()
            ctx = TestMessageContext.get()
            ctx.guild.roll_timeout = 0
            ctx.guild.current_roll = 333
            ctx.guild.allow_renaming = True
            ctx.guild.gambling_limit = None
            mock_roll.get_last_roll = AsyncMock(return_value=None)
            # Act
            with patch("dicebot.commands.roll.random") as mock_random:
                mock_random.randint.return_value = 333
                await roll.roll(ctx, GreedyStr(""))
            # Assert
            mock_roll.assert_called_once()
            mock_ban.ban_internal.assert_not_awaited()
            ctx.session.commit.assert_awaited()
            ctx.channel.send.assert_awaited()
            ctx.guild.add_chat_rename.assert_not_awaited()
            ctx.guild.add_guild_rename.assert_awaited_once()

    @patch("dicebot.commands.roll.Roll", autospec=True)
    @patch("dicebot.commands.roll.ban", autospec=True)
    async def test_roll_with_gambling(self, mock_ban, mock_roll) -> None:
        with self.subTest("negative"):
            # Arrange
            mock_roll.reset_mock()
            mock_ban.reset_mock()
            ctx = TestMessageContext.get()
            ctx.guild.roll_timeout = 0
            ctx.guild.current_roll = 333
            ctx.guild.allow_renaming = True
            ctx.guild.gambling_limit = None
            mock_roll.get_last_roll = AsyncMock(return_value=None)
            # Act
            with patch("dicebot.commands.roll.random") as mock_random:
                mock_random.randint.return_value = 333
                await roll.roll(ctx, GreedyStr("-5"))
            # Assert
            mock_roll.assert_not_called()
            mock_ban.ban_internal.assert_awaited_once()
            ctx.session.commit.assert_not_awaited()
            ctx.channel.send.assert_awaited()
            ctx.guild.add_chat_rename.assert_not_awaited()
            ctx.guild.add_guild_rename.assert_not_awaited()
        with self.subTest("too high"):
            # Arrange
            mock_roll.reset_mock()
            mock_ban.reset_mock()
            ctx = TestMessageContext.get()
            ctx.guild.roll_timeout = 0
            ctx.guild.current_roll = 333
            ctx.guild.allow_renaming = True
            ctx.guild.gambling_limit = None
            mock_roll.get_last_roll = AsyncMock(return_value=None)
            # Act
            with patch("dicebot.commands.roll.random") as mock_random:
                mock_random.randint.return_value = 333
                await roll.roll(ctx, GreedyStr("334"))
            # Assert
            mock_roll.assert_not_called()
            mock_ban.ban_internal.assert_not_awaited()
            ctx.session.commit.assert_not_awaited()
            ctx.channel.send.assert_awaited()
            ctx.guild.add_chat_rename.assert_not_awaited()
            ctx.guild.add_guild_rename.assert_not_awaited()
        with self.subTest("turboban"):
            # Arrange
            mock_roll.reset_mock()
            mock_ban.reset_mock()
            ctx = TestMessageContext.get()
            ctx.guild.roll_timeout = 0
            ctx.guild.current_roll = 333
            ctx.guild.allow_renaming = True
            ctx.guild.gambling_limit = None
            mock_roll.get_last_roll = AsyncMock(return_value=None)
            # Act
            with patch("dicebot.commands.roll.random") as mock_random:
                mock_random.randint.return_value = 123
                await roll.roll(ctx, GreedyStr("5"))
            # Assert
            mock_roll.assert_called()
            self.assertEqual(5, mock_roll.call_count)
            mock_ban.ban_internal.assert_not_awaited()
            mock_ban.turboban.assert_awaited_once()
            ctx.session.commit.assert_awaited()
            ctx.channel.send.assert_awaited()
            ctx.guild.add_chat_rename.assert_not_awaited()
            ctx.guild.add_guild_rename.assert_not_awaited()

    async def test_set_gambling_limit(self) -> None:
        with self.subTest("simple"):
            # Arrange
            ctx = TestMessageContext.get()
            # Act
            await roll.set_gambling_limit(ctx, 123)
            # Assert
            self.assertEqual(123, ctx.guild.gambling_limit)
            ctx.session.commit.assert_awaited_once()
            ctx.channel.send.assert_awaited_once()
        with self.subTest("negative"):
            # Arrange
            ctx = TestMessageContext.get()
            # Act
            await roll.set_gambling_limit(ctx, -1)
            # Assert
            self.assertIsNone(ctx.guild.gambling_limit)
            ctx.session.commit.assert_awaited_once()
            ctx.channel.send.assert_awaited_once()
