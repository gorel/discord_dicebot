#!/usr/bin/env python3

import asyncio
import logging
import os
import random

import aiohttp

from dicebot.commands import ban
from dicebot.core.register_command import register_command
from dicebot.data.types.bot_param import BotParam
from dicebot.data.types.greedy_str import GreedyStr
from dicebot.data.types.message_context import MessageContext
from dicebot.data.types.time import Time

ISSUES_URL = "https://api.github.com/repos/gorel/discord_dicebot/issues"
SUCCESS_CODE = 201

RANDOM_BAN_THRESHOLD = 0.20


async def _fileatask_real(ctx: MessageContext, title: str) -> None:
    """Add a new issue to the github repository"""
    headers = {"accept": "application/vnd.github+json"}
    user = os.getenv("GITHUB_USER", "")
    password = os.getenv("GITHUB_PASS", "")

    async with aiohttp.ClientSession() as session:
        async with session.post(
            ISSUES_URL, json={"title": title}, headers=headers, auth=aiohttp.BasicAuth(user, password)
        ) as r:
            json_resp = await r.json()
            if r.status == SUCCESS_CODE:
                response_url = json_resp["html_url"]
                await ctx.channel.send(
                    f"Your suggestion has been noted: {response_url}"
                )
            else:
                logging.error(f"Request to GitHub failed: {json_resp}")
                await ctx.channel.send(
                    f"Something went wrong submitting the issue to GitHub (status_code = {r.status})"
                )


async def _ban_helper(ctx: MessageContext, ban_message: str) -> None:
    await ctx.channel.send(
        ban_message,
        reference=ctx.message,
    )
    await asyncio.sleep(3)
    await ban.ban(
        ctx,
        target=ctx.author,
        timer=Time("1hr"),
        ban_as_bot=BotParam(True),
        reason=BotParam("Bad fileatask idea"),
    )


@register_command
async def fileatask(ctx: MessageContext, title: GreedyStr) -> None:
    """File a task against the GitHub repository... for the owner.
    Otherwise say something witty."""
    title_str = title.unwrap()
    owner_discord_id = int(os.getenv("OWNER_DISCORD_ID", 0))
    if ctx.message.author.id == owner_discord_id:
        await _fileatask_real(ctx, title_str)
    elif "fix" in title.split():
        await _ban_helper(
            ctx,
            "I'm not fixing this for you heathens.",
        )
    elif random.random() < RANDOM_BAN_THRESHOLD:
        await _ban_helper(
            ctx,
            "This is a bad idea and you should feel bad.",
        )
    elif ctx.author.is_currently_banned(ctx.session, ctx.guild):
        await ctx.channel.send("Your opinion does not matter.", reference=ctx.message)
    else:
        await ctx.channel.send(
            "Thanks for the suggestion! Adding it to the backlog.",
            reference=ctx.message,
        )
        logging.info("Sending suggestion to /dev/null")
