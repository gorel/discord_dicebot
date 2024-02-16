#!/usr/bin/env python3

from unittest.mock import AsyncMock, create_autospec

from dicebot.commands import macro
from dicebot.data.db.macro import Macro
from dicebot.data.types.greedy_str import GreedyStr
from dicebot.test.utils import DicebotTestCase, TestMessageContext


class TestMacro(DicebotTestCase):
    async def test_macro_add(self) -> None:
        with self.subTest("new macro"):
            # Arrange
            ctx = TestMessageContext.get()
            ctx.guild.get_macro = AsyncMock(return_value=None)
            # Act
            await macro.macro_add(ctx, "key", GreedyStr("value"))
            # Assert
            ctx.guild.add_macro.assert_awaited_once()
            ctx.session.commit.assert_awaited_once()
            ctx.channel.send.assert_awaited_once()
        with self.subTest("macro exists"):
            # Arrange
            ctx = TestMessageContext.get()
            ctx.guild.get_macro = AsyncMock(return_value=create_autospec(Macro))
            # Act
            await macro.macro_add(ctx, "key", GreedyStr("value"))
            # Assert
            ctx.guild.add_macro.assert_not_awaited()
            ctx.session.commit.assert_not_awaited()
            ctx.channel.send.assert_awaited_once()

    async def test_macro_del(self) -> None:
        with self.subTest("new macro"):
            # Arrange
            ctx = TestMessageContext.get()
            ctx.guild.get_macro = AsyncMock(return_value=None)
            # Act
            await macro.macro_del(ctx, "key")
            # Assert
            ctx.session.commit.assert_not_awaited()
            ctx.channel.send.assert_awaited_once()
        with self.subTest("macro exists"):
            # Arrange
            ctx = TestMessageContext.get()
            mock_macro = create_autospec(Macro)
            ctx.guild.get_macro = AsyncMock(return_value=mock_macro)
            # Act
            await macro.macro_del(ctx, "key")
            # Assert
            ctx.session.delete.assert_awaited_once_with(mock_macro)
            ctx.session.commit.assert_awaited_once()
            ctx.channel.send.assert_awaited_once()

    async def test_m(self) -> None:
        with self.subTest("new macro"):
            # Arrange
            ctx = TestMessageContext.get()
            ctx.guild.get_macro = AsyncMock(return_value=None)
            # Act
            await macro.m(ctx, "key")
            # Assert
            ctx.channel.send.assert_awaited_once()
        with self.subTest("macro exists"):
            # Arrange
            ctx = TestMessageContext.get()
            mock_macro = create_autospec(Macro)
            ctx.guild.get_macro = AsyncMock(return_value=mock_macro)
            # Act
            await macro.m(ctx, "key")
            # Assert
            ctx.channel.send.assert_awaited_once_with(mock_macro.value)