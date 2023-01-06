#!/usr/bin/env python3

import asyncio
import datetime
import unittest

from dicebot.commands import birthday
from dicebot.data.types.greedy_str import GreedyStr
from dicebot.test.utils import TestMessageContext


class TestBirthday(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        await super().asyncSetUp()
        asyncio.get_running_loop().set_debug(False)

    async def test_birthday(self) -> None:
        with self.subTest("valid"):
            # Arrange
            ctx = TestMessageContext.get()
            now = datetime.datetime.now()
            birthday_str = "July 5"
            expected = datetime.datetime(year=now.year, month=7, day=5)
            # Act
            await birthday.birthday(ctx, GreedyStr(birthday_str))
            # Assert
            self.assertEqual(expected, ctx.author.birthday)
            ctx.session.commit.assert_awaited()
            ctx.channel.send.assert_awaited_once()
        with self.subTest("invalid"):
            # Arrange
            ctx = TestMessageContext.get()
            now = datetime.datetime.now()
            birthday_str = "Octuembre 32"
            # Act
            await birthday.birthday(ctx, GreedyStr(birthday_str))
            # Assert
            ctx.session.commit.assert_not_awaited()
            ctx.channel.send.assert_awaited_once()
