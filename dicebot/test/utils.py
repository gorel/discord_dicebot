#!/usr/bin/env python3

from __future__ import annotations

from typing import Optional
from unittest.mock import create_autospec

import discord
from sqlalchemy.ext.asyncio import AsyncSession

from dicebot.data.db.guild import Guild
from dicebot.data.db.user import User
from dicebot.data.types.message_context import MessageContext


class TestMessageContext(MessageContext):
    @classmethod
    def get(
        cls,
        message_content: str = "!dummy",
        reaction: Optional[discord.Reaction] = None,
    ) -> TestMessageContext:
        message = create_autospec(discord.Message)
        message.content = message_content
        return cls(
            client=create_autospec(discord.Client),
            session=create_autospec(AsyncSession),
            author=create_autospec(User),
            guild=create_autospec(Guild),
            message=message,
            reactor=create_autospec(User),
            reaction=reaction,
            is_test=True,
        )
