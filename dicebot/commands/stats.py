#!/usr/bin/env python3

from __future__ import annotations

from typing import Optional

import discord
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from dicebot.commands import timezone
from dicebot.core.register_command import register_command
from dicebot.data.db.ban import Ban
from dicebot.data.db.pun import Pun
from dicebot.data.db.rep import Rep
from dicebot.data.db.roll import Roll
from dicebot.data.db.thanks import Thanks
from dicebot.data.db.user import User
from dicebot.data.types.message_context import MessageContext


async def get_roll_stats(
    session: AsyncSession, guild, user: User
) -> dict:
    result = await session.scalars(
        select(Roll).filter_by(guild_id=guild.id, discord_user_id=user.id)
    )
    rolls = result.all()

    if not rolls:
        return {
            "total": 0,
            "wins": 0,
            "losses": 0,
            "win_rate": "0%",
            "best": 0,
            "last_roll": "Never",
        }

    total = len(rolls)
    wins = sum(1 for r in rolls if r.actual_roll >= r.target_roll)
    losses = total - wins
    win_rate = f"{100 * wins / total:.1f}%"
    best = max(r.actual_roll for r in rolls)
    last_dt = max(r.rolled_at for r in rolls)
    last_roll = last_dt.strftime("%b %d, %Y")

    return {
        "total": total,
        "wins": wins,
        "losses": losses,
        "win_rate": win_rate,
        "best": best,
        "last_roll": last_roll,
    }


async def get_ban_stats(
    session: AsyncSession, guild, user: User
) -> dict:
    result = await session.scalars(
        select(Ban).filter_by(guild_id=guild.id, bannee_id=user.id)
    )
    bans = result.all()
    times_banned = len(bans)

    is_banned = await user.is_currently_banned(session, guild)
    if is_banned:
        latest = await Ban.get_latest_unvoided_ban(session, guild, user)
        until_str = timezone.localize_dt(latest.banned_until, guild.timezone)
        currently_banned = f"Yes (until {until_str})"
    else:
        currently_banned = "No"

    is_immune = await user.is_currently_immune(session, guild)
    immune = "Yes" if is_immune else "No"

    return {
        "times_banned": times_banned,
        "currently_banned": currently_banned,
        "immune": immune,
    }


async def get_social_stats(
    session: AsyncSession, guild, user: User
) -> dict:
    thanks_given_result = await session.execute(
        select(func.count()).select_from(Thanks).filter_by(
            guild_id=guild.id, thanker_id=user.id
        )
    )
    thanks_given = thanks_given_result.scalar() or 0

    thanks_received_result = await session.execute(
        select(func.count()).select_from(Thanks).filter_by(
            guild_id=guild.id, thankee_id=user.id
        )
    )
    thanks_received = thanks_received_result.scalar() or 0

    puns_caught_result = await session.execute(
        select(func.count()).select_from(Pun).filter_by(
            guild_id=guild.id, first_poster_id=user.id
        )
    )
    puns_caught = puns_caught_result.scalar() or 0

    return {
        "thanks_given": thanks_given,
        "thanks_received": thanks_received,
        "puns_caught": puns_caught,
    }


async def get_rep_stats(
    session: AsyncSession, guild, user: User
) -> dict:
    received = await Rep.get_total_received(session, guild.id, user.id)
    given = await Rep.get_total_given(session, guild.id, user.id)

    biggest_fan_data = await Rep.get_biggest_fan(session, guild.id, user.id)
    biggest_fan = "No one yet"
    if biggest_fan_data is not None:
        fan_id, fan_total = biggest_fan_data
        biggest_fan = f"<@{fan_id}> ({fan_total:+d})"

    hater_data = await Rep.get_hater(session, guild.id, user.id)
    hater = "No haters yet"
    if hater_data is not None:
        hater_id, hater_total = hater_data
        hater = f"<@{hater_id}> ({hater_total:+d})"

    best_friend_data = await Rep.get_best_friend(session, guild.id, user.id)
    best_friend = "No one yet"
    if best_friend_data is not None:
        friend_id, friend_total = best_friend_data
        best_friend = f"<@{friend_id}> ({friend_total:+d})"

    nemesis_data = await Rep.get_nemesis(session, guild.id, user.id)
    nemesis = "No nemesis yet"
    if nemesis_data is not None:
        nemesis_id, nemesis_total = nemesis_data
        nemesis = f"<@{nemesis_id}> ({nemesis_total:+d})"

    return {
        "received": received,
        "given": given,
        "biggest_fan": biggest_fan,
        "hater": hater,
        "best_friend": best_friend,
        "nemesis": nemesis,
    }


@register_command
async def stats(ctx: MessageContext, target: Optional[User] = None) -> None:
    """Show stats for a user (defaults to yourself). Usage: !stats [@user]"""
    if target is None:
        target = ctx.author

    roll_stats = await get_roll_stats(ctx.session, ctx.guild, target)
    ban_stats = await get_ban_stats(ctx.session, ctx.guild, target)
    social_stats = await get_social_stats(ctx.session, ctx.guild, target)
    rep_stats = await get_rep_stats(ctx.session, ctx.guild, target)

    is_banned = ban_stats["currently_banned"] != "No"
    color = discord.Color.red() if is_banned else discord.Color.blue()

    # Try to get a display name from the Discord guild
    display_name = f"<@{target.id}>"
    if ctx.discord_guild is not None:
        member = ctx.discord_guild.get_member(target.id)
        if member is not None:
            display_name = member.display_name

    embed = discord.Embed(
        title=f"Stats for {display_name}",
        color=color,
    )

    # Roll Stats section
    embed.add_field(name="\u200b", value="**🎲 Roll Stats**", inline=False)
    embed.add_field(name="Total Rolls", value=str(roll_stats["total"]), inline=True)
    embed.add_field(name="Win Rate", value=roll_stats["win_rate"], inline=True)
    embed.add_field(name="Wins", value=str(roll_stats["wins"]), inline=True)
    embed.add_field(name="Losses", value=str(roll_stats["losses"]), inline=True)
    embed.add_field(name="Best Roll", value=str(roll_stats["best"]), inline=True)
    embed.add_field(name="Last Roll", value=roll_stats["last_roll"], inline=True)

    # Ban Stats section
    embed.add_field(name="\u200b", value="**🔨 Ban Stats**", inline=False)
    embed.add_field(name="Times Banned", value=str(ban_stats["times_banned"]), inline=False)
    embed.add_field(name="Currently Banned", value=ban_stats["currently_banned"], inline=True)
    embed.add_field(name="Ban Immune", value=ban_stats["immune"], inline=True)

    # Social Stats section
    embed.add_field(name="\u200b", value="**🙏 Social Stats**", inline=False)
    embed.add_field(name="Thanks Given", value=str(social_stats["thanks_given"]), inline=True)
    embed.add_field(name="Thanks Received", value=str(social_stats["thanks_received"]), inline=True)
    embed.add_field(name="Puns Caught", value=str(social_stats["puns_caught"]), inline=True)

    # Rep Stats section
    embed.add_field(name="\u200b", value="**⭐ Rep Stats**", inline=False)
    embed.add_field(name="Rep Received", value=f"{rep_stats['received']:+d}", inline=True)
    embed.add_field(name="Rep Given", value=f"{rep_stats['given']:+d}", inline=True)
    embed.add_field(name="\u200b", value="\u200b", inline=True)
    embed.add_field(name="Biggest Fan", value=rep_stats["biggest_fan"], inline=True)
    embed.add_field(name="Hater", value=rep_stats["hater"], inline=True)
    embed.add_field(name="Best Friend", value=rep_stats["best_friend"], inline=True)
    embed.add_field(name="Nemesis", value=rep_stats["nemesis"], inline=True)

    await ctx.send(embed=embed)
