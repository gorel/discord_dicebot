#!/usr/bin/env python3

from unittest.mock import AsyncMock, patch

from dicebot.commands import giffer
from dicebot.data.types.greedy_str import GreedyStr
from dicebot.test.utils import DicebotTestCase, TestMessageContext


class TestGiffer(DicebotTestCase):
    @patch("dicebot.commands.giffer.TenorGifRetriever", autospec=True)
    async def test_get_random_gif_url(self, mock_retriever) -> None:
        with self.subTest("simple"):
            # Arrange
            mock_retriever().get = AsyncMock(return_value=["url1"])
            # Act
            actual = await giffer.get_random_gif_url("a b c")
            # Assert
            self.assertEqual("url1", actual)
        with self.subTest("no results"):
            # Arrange
            mock_retriever().get = AsyncMock(return_value=[])
            # Act
            actual = await giffer.get_random_gif_url("a b c")
            # Assert
            self.assertIsNone(actual)

    @patch("dicebot.commands.giffer.get_random_gif_url", return_value="url1")
    async def test_gif(self, mock_get_random_gif_url) -> None:
        # Arrange
        ctx = TestMessageContext.get()
        # Act
        await giffer.gif(ctx, GreedyStr("a b c"))
        # Assert
        ctx.send.assert_awaited_once_with(mock_get_random_gif_url.return_value)
