#!/usr/bin/env python3

import asyncio
import unittest
from unittest.mock import patch

from dicebot.commands import meme
from dicebot.data.types.greedy_str import GreedyStr
from dicebot.test.utils import TestMessageContext


class TestMeme(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        await super().asyncSetUp()
        asyncio.get_running_loop().set_debug(False)

    @patch("dicebot.commands.meme.MemeGenerator")
    async def test_meme_simple(self, mock_memegenerator) -> None:
        # Arrange
        ctx = TestMessageContext.get()
        expected_template = "template"
        expected_args = ["arg1", "arg2", "arg3"]
        # Act
        with patch("dicebot.commands.meme.MemeFactory"):
            await meme.meme(ctx, GreedyStr("template arg1 arg2 arg3"))
        # Assert
        mock_memegenerator.get_meme_image_bytes.assert_called_once_with(
            expected_template, expected_args
        )
        ctx.channel.send.assert_awaited_once()

    @patch("dicebot.commands.meme.MemeGenerator")
    async def test_meme_list(self, mock_memegenerator) -> None:
        # Arrange
        ctx = TestMessageContext.get()
        # Act
        with patch("dicebot.commands.meme.MemeFactory"):
            await meme.meme(ctx, GreedyStr("list"))
        # Assert
        mock_memegenerator.get_meme_image_bytes.assert_not_called()
        ctx.channel.send.assert_awaited_once()

    @patch("dicebot.commands.meme.MemeFactory")
    @patch("dicebot.commands.meme.MemeGenerator")
    async def test_meme_unknown(self, mock_memegenerator, mock_memefactory) -> None:
        # Arrange
        ctx = TestMessageContext.get()
        mock_memefactory.MemeLib.get.return_value = None
        # Act
        await meme.meme(ctx, GreedyStr("list"))
        # Assert
        mock_memegenerator.get_meme_image_bytes.assert_not_called()
        ctx.channel.send.assert_awaited_once()
