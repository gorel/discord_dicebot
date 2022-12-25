#!/usr/bin/env python3

import logging
import os

from discord import TextChannel

from dicebot.commands.admin import requires_admin
from dicebot.core.register_command import register_command
from dicebot.data.db.guild import Guild
from dicebot.data.types.greedy_str import GreedyStr
from dicebot.data.types.message_context import MessageContext


@requires_admin
@register_command
async def announce(ctx: MessageContext, announcement: GreedyStr) -> None:
    """Send an announcement to all servers where this bot is running.
    This method is only usable by the bot owner and is intended for critical updates."""
    owner_discord_id = int(os.getenv("OWNER_DISCORD_ID", 0))
    if ctx.message.author.id == owner_discord_id:
        for db_guild in await Guild.get_all_for_announcements(ctx.session):
            if ctx.is_test and db_guild.id != ctx.guild.id:
                logging.info("Skipping announcement for other channels in test mode")
                continue

            guild = await ctx.client.fetch_guild(db_guild.id)
            channel = None

            if db_guild.primary_text_channel is not None:
                try:
                    channel = await guild.fetch_channel(db_guild.primary_text_channel)
                    if not isinstance(channel, TextChannel):
                        logging.warning(
                            f"Primary text channel for guild {db_guild.id} "
                            "is not a TextChannel"
                        )
                        channel = None
                except Exception as e:
                    logging.warning(
                        f"While fetching primary text channel for guild {db_guild.id},"
                        f"got error: {e}"
                    )
                    channel = None

            # Either the guild has no saved primary_text_channel
            # or the above block resulted in an invalid channel
            if channel is None:
                logging.info(f"No default announcement channel for guild {db_guild.id}")
                # We need to call fetch since the channels may not be loaded yet
                all_channels = await guild.fetch_channels()
                text_channels = [c for c in all_channels if isinstance(c, TextChannel)]
                if len(text_channels) == 0:
                    logging.warning(f"Guild {guild.id} has no available text channels")
                    continue
                channel = text_channels[0]
                msg = "**NOTE**: An admin can disable bot announcements with "
                msg += "`!disable_announcements`\n"
                msg += "Suppress this message by typing `!set_announce_channel` in the "
                msg += "channel where you'd like to receive announcements from the bot."
                await channel.send(msg)

            await channel.send(announcement)


@requires_admin
@register_command
async def set_announce_channel(ctx: MessageContext) -> None:
    """Sets the TextChannel where this command was sent as the default channel for
    announcements from the bot."""
    ctx.guild.primary_text_channel = ctx.channel.id
    await ctx.session.commit()
    await ctx.channel.send("From now on, announcements will be sent to this channel")


@requires_admin
@register_command
async def disable_announcements(ctx: MessageContext) -> None:
    """Turns off announcements sent by the bot from being present in this server"""
    ctx.guild.disable_announcements = True
    await ctx.session.commit()
    await ctx.channel.send("Announcements for this server have been disabled")
