#!/usr/bin/env python3

import discord
from sqlalchemy.ext.asyncio import AsyncSession

from dicebot.core.guild_context import GuildContext
from dicebot.data.db_models import Guild


class ServerManager:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def handle_message(
        self,
        client: discord.Client,
        message: discord.Message,
    ) -> None:
        if isinstance(message.channel, discord.DMChannel):
            guild = await Guild.get_or_create(
                self.session, message.channel.id, is_dm=True
            )
            ctx = GuildContext(client, guild, self.session)
            await ctx.handle_dm(message)
        else:
            guild = await Guild.get_or_create(
                self.session, message.channel.guild.id, is_dm=False
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
            guild = await Guild.get_or_create(
                self.session, reaction.message.channel.id, is_dm=True
            )
        else:
            guild = await Guild.get_or_create(
                self.session, reaction.message.channel.guild.id, is_dm=False
            )

        ctx = GuildContext(client, guild, self.session)
        await ctx.handle_reaction_add(reaction, user)
