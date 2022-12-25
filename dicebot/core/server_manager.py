#!/usr/bin/env python3

import discord
from sqlalchemy.ext.asyncio import AsyncSession

from dicebot.core.guild_context import GuildContext
from dicebot.data.db.guild import Guild


class UnsupportedChannelException(ValueError):
    pass


class ServerManager:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def handle_message(
        self,
        client: discord.Client,
        message: discord.Message,
    ) -> None:
        if isinstance(message.channel, discord.DMChannel):
            # For a DM, the person who sent it is the owner
            guild = await Guild.get_or_create(
                session=self.session,
                guild_id=message.channel.id,
                owner_id=message.author.id,
                is_dm=True,
            )
            ctx = GuildContext(client, guild, self.session)
            await ctx.handle_dm(message)
        else:
            if message.channel.guild is None:
                raise UnsupportedChannelException(
                    "The bot is not available in this kind of context"
                )
            if message.channel.guild.owner is None:
                raise UnsupportedChannelException(
                    "The bot is not available in guilds without an owner"
                )
            guild = await Guild.get_or_create(
                session=self.session,
                guild_id=message.channel.guild.id,
                owner_id=message.channel.guild.owner.id,
                is_dm=False,
            )
            ctx = GuildContext(client, guild, self.session)
            await ctx.handle_message(message)

    async def handle_reaction_add(
        self,
        client: discord.Client,
        reaction: discord.Reaction,
        user: discord.User,
    ) -> None:
        if isinstance(reaction.message.channel, discord.DMChannel):
            # For a DM, the person who sent it is the owner
            guild = await Guild.get_or_create(
                session=self.session,
                guild_id=reaction.message.channel.id,
                owner_id=reaction.message.author.id,
                is_dm=True,
            )
        else:
            if reaction.message.channel.guild is None:
                raise UnsupportedChannelException(
                    "The bot is not available in this kind of context"
                )
            if reaction.message.channel.guild.owner is None:
                raise UnsupportedChannelException(
                    "The bot is not available in guilds without an owner"
                )
            guild = await Guild.get_or_create(
                session=self.session,
                guild_id=reaction.message.channel.guild.id,
                owner_id=reaction.message.channel.guild.owner.id,
                is_dm=False,
            )

        ctx = GuildContext(client, guild, self.session)
        await ctx.handle_reaction_add(reaction, user)
