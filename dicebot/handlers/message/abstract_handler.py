#!/usr/bin/env python3

import logging
from abc import ABC, abstractmethod

from discord import Emoji

from dicebot.data.types.message_context import MessageContext


class AbstractHandler(ABC):
    @abstractmethod
    async def should_handle(
        self,
        ctx: MessageContext,
    ) -> bool:
        pass

    @abstractmethod
    async def handle(
        self,
        ctx: MessageContext,
    ) -> None:
        pass

    async def should_handle_no_throw(self, ctx: MessageContext) -> bool:
        try:
            return await self.should_handle(ctx)
        except Exception as e:
            logging.exception(
                f"Exception raised in should_handle for {self.__class__.__name__}: {e}"
            )
            return False

    async def handle_no_throw(self, ctx: MessageContext) -> None:
        try:
            await self.handle(ctx)
        except Exception as e:
            logging.exception(
                f"Exception raised in handle for {self.__class__.__name__}: {e}"
            )

    def get_emoji_by_name(self, ctx: MessageContext, name: str) -> Emoji | None:
        guild = ctx.message.guild
        if guild is None:
            return None

        guild_emojis = {e.name.lower(): e for e in guild.emojis}
        all_emojis = {e.name.lower(): e for e in ctx.client.emojis}
        if name in guild_emojis.keys():
            return guild_emojis[name]
        elif name in all_emojis.keys():
            return all_emojis[name]
        return None
