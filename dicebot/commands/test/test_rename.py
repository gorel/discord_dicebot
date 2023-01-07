#!/usr/bin/env python3

import asyncio
import unittest
from unittest.mock import AsyncMock, create_autospec, patch

from discord import DMChannel

from dicebot.commands import rename
from dicebot.data.db.rename import Rename
from dicebot.data.types.greedy_str import GreedyStr
from dicebot.test.utils import TestMessageContext


class TestRename(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        await super().asyncSetUp()
        asyncio.get_running_loop().set_debug(False)

    @patch("dicebot.commands.rename.Rename")
    async def test_rename(self, mock_rename) -> None:

        with self.subTest("winner"):
            # Arrange
            ctx = TestMessageContext.get()
            mock_win = create_autospec(
                Rename, rename_used=False, discord_user_id=ctx.author_id
            )
            mock_rename.get_last_winner = AsyncMock(return_value=mock_win)
            mock_rename.get_last_loser = AsyncMock(return_value=None)
            # Act
            await rename.rename(ctx, GreedyStr("new name"))
            # Assert
            ctx.session.commit.assert_awaited_once()
            assert ctx.discord_guild is not None
            ctx.discord_guild.edit.assert_awaited_once()
        with self.subTest("loser"):
            # Arrange
            ctx = TestMessageContext.get()
            mock_lose = create_autospec(
                Rename, rename_used=False, discord_user_id=ctx.author_id
            )
            mock_rename.get_last_winner = AsyncMock(return_value=None)
            mock_rename.get_last_loser = AsyncMock(return_value=mock_lose)
            # Act
            await rename.rename(ctx, GreedyStr("new name"))
            # Assert
            ctx.session.commit.assert_awaited_once()
            ctx.channel.edit.assert_awaited_once()  # type: ignore
        with self.subTest("neither"):
            # Arrange
            ctx = TestMessageContext.get()
            mock_rename.get_last_winner = AsyncMock(return_value=None)
            mock_rename.get_last_loser = AsyncMock(return_value=None)
            # Act
            await rename.rename(ctx, GreedyStr("new name"))
            # Assert
            ctx.channel.send.assert_awaited_once()
            ctx.session.commit.assert_not_awaited()
        with self.subTest("dm channel"):
            # Arrange
            ctx = TestMessageContext.get()
            mock_win = create_autospec(
                Rename, rename_used=False, discord_user_id=ctx.author_id
            )
            ctx.message.channel = create_autospec(DMChannel)
            mock_rename.get_last_winner = AsyncMock(return_value=mock_win)
            mock_rename.get_last_loser = AsyncMock(return_value=None)
            # Act & Assert
            with self.assertRaises(rename.RenameError):
                await rename.rename(ctx, GreedyStr("new name"))
