#!/usr/bin/env python3

from __future__ import annotations

import asyncio
import logging
import os
import unittest
from typing import Optional
from unittest.mock import AsyncMock, create_autospec

import discord
from sqlalchemy.ext.asyncio import AsyncSession

from dicebot.data.db.guild import Guild
from dicebot.data.db.user import User
from dicebot.data.types.message_context import MessageContext


class DicebotTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        await super().asyncSetUp()
        logging.disable(logging.CRITICAL)
        asyncio.get_running_loop().set_debug(False)


class TestMessageContext(MessageContext):
    @property
    def channel(self):
        return self.message.channel

    @classmethod
    def get(
        cls,
        message_content: str = "!dummy",
        reaction: Optional[discord.Reaction] = None,
    ) -> TestMessageContext:
        message = create_autospec(discord.Message)
        message.channel = AsyncMock()
        message.content = message_content
        res = cls(
            client=create_autospec(discord.Client),
            session=create_autospec(AsyncSession),
            author=create_autospec(User, id=int(os.getenv("OWNER_DISCORD_ID", 0))),
            guild=create_autospec(Guild),
            discord_guild=create_autospec(discord.Guild),
            message=message,
            reactor=create_autospec(User),
            reaction=reaction,
            is_test=True,
        )
        res.quote_reply = AsyncMock()
        return res
