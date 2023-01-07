#!/usr/bin/env python3

import asyncio
import unittest
from unittest.mock import patch

from dicebot.commands import fileatask
from dicebot.data.types.greedy_str import GreedyStr
from dicebot.test.utils import TestMessageContext


class TestFileatask(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        await super().asyncSetUp()
        asyncio.get_running_loop().set_debug(False)

    async def test_fileatask_real(self) -> None:
        pass

    @patch("dicebot.commands.fileatask.ban", autospec=True)
    async def test_ban_helper(self, mock_ban) -> None:
        # Arrange
        ctx = TestMessageContext.get()
        # Act
        await fileatask._ban_helper(ctx, "ban message")
        # Assert
        ctx.quote_reply.assert_awaited_once()
        mock_ban.ban_internal.assert_awaited_once()

    @patch("dicebot.commands.fileatask._fileatask_real", autospec=True)
    @patch("dicebot.commands.fileatask._ban_helper", autospec=True)
    @patch("dicebot.commands.fileatask.giffer", autospec=True)
    async def test_fileatask(
        self, mock_giffer, mock_ban_helper, mock_fileatask_real
    ) -> None:
        with self.subTest("real"):
            # Arrange
            mock_giffer.reset_mock()
            mock_ban_helper.reset_mock()
            mock_fileatask_real.reset_mock()
            ctx = TestMessageContext.get()
            ctx.author.id = 12345
            # Act
            with patch("dicebot.commands.fileatask.os") as mock_os:
                mock_os.getenv.return_value = ctx.author.id
                await fileatask.fileatask(ctx, GreedyStr("implement thing"))
            # Assert
            mock_fileatask_real.assert_awaited_once()
        with self.subTest("fix"):
            # Arrange
            mock_giffer.reset_mock()
            mock_ban_helper.reset_mock()
            mock_fileatask_real.reset_mock()
            ctx = TestMessageContext.get()
            ctx.author.id = 12345
            # Act
            await fileatask.fileatask(ctx, GreedyStr("fix thing"))
            # Assert
            mock_ban_helper.assert_awaited_once()
            mock_fileatask_real.assert_not_awaited()
        with self.subTest("currently banned"):
            # Arrange
            mock_giffer.reset_mock()
            mock_ban_helper.reset_mock()
            mock_fileatask_real.reset_mock()
            ctx = TestMessageContext.get()
            ctx.author.is_currently_banned.return_value = True
            ctx.author.id = 12345
            # Act
            await fileatask.fileatask(ctx, GreedyStr("implement thing"))
            # Assert
            ctx.quote_reply.assert_awaited_once()
            mock_fileatask_real.assert_not_awaited()
        with self.subTest("trash gif"):
            # Arrange
            mock_giffer.reset_mock()
            mock_ban_helper.reset_mock()
            mock_fileatask_real.reset_mock()
            ctx = TestMessageContext.get()
            ctx.author.is_currently_banned.return_value = False
            ctx.author.id = 12345
            # Act
            with patch("dicebot.commands.fileatask.random") as mock_random:
                mock_random.random.return_value = (
                    fileatask.RANDOM_TRASH_GIF_THRESHOLD - 0.01
                )
                await fileatask.fileatask(ctx, GreedyStr("implement thing"))
            # Assert
            mock_giffer.gif.assert_awaited_once()
            mock_ban_helper.assert_not_awaited()
            mock_fileatask_real.assert_not_awaited()
        with self.subTest("random ban"):
            # Arrange
            mock_giffer.reset_mock()
            mock_ban_helper.reset_mock()
            mock_fileatask_real.reset_mock()
            ctx = TestMessageContext.get()
            ctx.author.is_currently_banned.return_value = False
            ctx.author.id = 12345
            # Act
            with patch("dicebot.commands.fileatask.random") as mock_random:
                mock_random.random.side_effect = [
                    fileatask.RANDOM_TRASH_GIF_THRESHOLD + 0.01,
                    fileatask.RANDOM_BAN_THRESHOLD - 0.01,
                ]
                await fileatask.fileatask(ctx, GreedyStr("implement thing"))
            # Assert
            mock_giffer.gif.assert_not_awaited()
            mock_ban_helper.assert_awaited_once()
            mock_fileatask_real.assert_not_awaited()
        with self.subTest("backlog"):
            # Arrange
            mock_giffer.reset_mock()
            mock_ban_helper.reset_mock()
            mock_fileatask_real.reset_mock()
            ctx = TestMessageContext.get()
            ctx.author.is_currently_banned.return_value = False
            ctx.author.id = 12345
            # Act
            with patch("dicebot.commands.fileatask.random") as mock_random:
                mock_random.random.side_effect = [
                    fileatask.RANDOM_TRASH_GIF_THRESHOLD + 0.01,
                    fileatask.RANDOM_BAN_THRESHOLD + 0.01,
                ]
                await fileatask.fileatask(ctx, GreedyStr("implement thing"))
            # Assert
            mock_giffer.gif.assert_not_awaited()
            mock_ban_helper.assert_not_awaited()
            mock_fileatask_real.assert_not_awaited()
            ctx.quote_reply.assert_awaited_once()
