#!/usr/bin/env python3

import logging
from abc import ABC, abstractmethod

import discord

import db_helper
from message_context import MessageContext


class AbstractReactionHandler(ABC):
    @property
    @abstractmethod
    def reaction_name(self) -> str:
        pass

    async def should_handle(
        self,
        reaction: discord.Reaction,
        user: discord.User,
        ctx: MessageContext,
    ) -> bool:
        is_proper_emoji = (
            not isinstance(reaction.emoji, str)
            and reaction.emoji.name.lower() == self.reaction_name
        )
        if not is_proper_emoji:
            return False

        # Pyre doesn't realize this can't be a string now
        assert not isinstance(reaction.emoji, str)

        # Check if this message has been reacted before
        reacted_before = db_helper.has_message_been_reacted(
            ctx.db_conn,
            reaction.message.guild.id,
            reaction.message.id,
            reaction.emoji.id,
        )
        if reacted_before:
            logging.warning("New reaction on message but it was reacted before.")
            return False

        # Only handle if we've hit the reaction threshold
        return reaction.count == ctx.server_ctx.reaction_threshold

    @abstractmethod
    async def handle(
        self,
        reaction: discord.Reaction,
        user: discord.User,
        ctx: MessageContext,
    ) -> None:
        pass

    async def record_handled(
        self,
        reaction: discord.Reaction,
        user: discord.User,
        ctx: MessageContext,
    ) -> None:
        # TODO: Replace with aiosqlite
        db_helper.record_reacted_message(
            ctx.db_conn,
            reaction.message.guild.id,
            reaction.message.id,
            reaction.emoji.id,
        )

    async def handle_and_record_no_throw(
        self,
        reaction: discord.Reaction,
        user: discord.User,
        ctx: MessageContext,
    ) -> None:
        try:
            if await self.should_handle(reaction, user, ctx):
                await self.handle(reaction, user, ctx)
                await self.record_handled(reaction, user, ctx)
        except Exception as e:
            logging.exception(
                f"Exception raised in handle_and_record for {self.__class__.__name__}: {e}"
            )
