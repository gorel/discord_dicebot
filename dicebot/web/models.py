#!/usr/bin/env python3

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import List, Optional

import discord
from sqlalchemy.ext.asyncio import AsyncSession

from dicebot.data.db.guild import Guild
from dicebot.web import app_ctx


@dataclass
class RelevantGuild:
    ctx: CombinedGuildContext
    is_admin: bool

    @classmethod
    async def get_subset_from_list(
        cls, user: Optional[discord.User], guilds: List[CombinedGuildContext]
    ) -> List[RelevantGuild]:
        if user is None:
            return [RelevantGuild(ctx, is_admin=False) for ctx in guilds]

        res = []
        for ctx in guilds:
            if await ctx.is_member(user):
                if await ctx.is_admin(user):
                    res.append(RelevantGuild(ctx, is_admin=True))
                else:
                    res.append(RelevantGuild(ctx, is_admin=False))
        return res


class CombinedGuildContext:
    def __init__(self, db_guild: Guild, discord_guild: discord.Guild) -> None:
        self.db = db_guild
        self.discord = discord_guild

    async def is_admin(self, user: discord.User) -> bool:
        admins = [u.id for u in self.db.admins]
        return user.id in admins

    async def get_member(self, user_id: int) -> Optional[discord.Member]:
        cached = self.discord.get_member(user_id)
        return cached or await self.discord.fetch_member(user_id)

    async def is_member(self, user: discord.User) -> bool:
        fetched_member = await self.get_member(user.id)
        return fetched_member is not None

    @classmethod
    async def _get_discord_guild(cls, guild_id: int) -> discord.Guild:
        cached = app_ctx.discord_client.get_guild(guild_id)
        return cached or await app_ctx.discord_client.fetch_guild(guild_id)

    @classmethod
    async def get(
        cls, session: AsyncSession, guild_id: int
    ) -> Optional[CombinedGuildContext]:
        db_guild = await Guild.get_or_none(session, guild_id)
        if db_guild is None:
            return None
        discord_guild = await cls._get_discord_guild(guild_id)
        return cls(db_guild, discord_guild)

    @classmethod
    async def get_all(cls, session: AsyncSession) -> List[CombinedGuildContext]:
        db_guilds = await Guild.get_all(session)
        db_map = {g.id: g for g in db_guilds}
        tasks = [cls._get_discord_guild(g.id) for g in db_guilds]
        fetched_guilds = await asyncio.gather(*tasks)
        di_map = {g.id: g for g in fetched_guilds}
        return [CombinedGuildContext(db_map[g.id], di_map[g.id]) for g in db_guilds]
