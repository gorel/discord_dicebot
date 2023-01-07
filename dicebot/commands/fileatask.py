#!/usr/bin/env python3

import asyncio
import logging
import os
import random

import aiohttp

from dicebot.commands import ban, giffer
from dicebot.core.register_command import register_command
from dicebot.data.types.greedy_str import GreedyStr
from dicebot.data.types.message_context import MessageContext
from dicebot.data.types.time import Time

ISSUES_URL = "https://api.github.com/repos/gorel/discord_dicebot/issues"
SUCCESS_CODE = 201

RANDOM_TRASH_GIF_THRESHOLD = 0.10
RANDOM_BAN_THRESHOLD = 0.10


async def _fileatask_real(ctx: MessageContext, title: str) -> None:
    """Add a new issue to the github repository"""
    headers = {"accept": "application/vnd.github+json"}
    user = os.getenv("GITHUB_USER", "")
    password = os.getenv("GITHUB_PASS", "")

    async with aiohttp.ClientSession() as session:
        async with session.post(
            ISSUES_URL,
            json={"title": title},
            headers=headers,
            auth=aiohttp.BasicAuth(user, password),
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
                    "Something went wrong submitting the issue "
                    f"to GitHub (status_code = {r.status})"
                )


async def _ban_helper(ctx: MessageContext, ban_message: str) -> None:
    await ctx.quote_reply(ban_message)
    await asyncio.sleep(3)
    await ban.ban_internal(
        ctx,
        target=ctx.author,
        timer=Time("1hr"),
        ban_as_bot=True,
        reason="Bad fileatask idea",
    )


@register_command
async def fileatask(ctx: MessageContext, title: GreedyStr) -> None:
    """File a task against the GitHub repository... for the owner.
    Otherwise say something witty."""
    title_str = title.unwrap()
    owner_discord_id = int(os.getenv("OWNER_DISCORD_ID", 0))
    if ctx.author_id == owner_discord_id:
        await _fileatask_real(ctx, title_str)
    elif "fix" in title.split():
        await _ban_helper(
            ctx,
            "I'm not fixing this for you heathens.",
        )
    elif await ctx.author.is_currently_banned(ctx.session, ctx.guild):
        await ctx.quote_reply("You are banned. Your opinion does not matter.")
    elif random.random() < RANDOM_TRASH_GIF_THRESHOLD:
        await ctx.channel.send("Oh yeah, I'll get *right* on that.")
        await giffer.gif(ctx, GreedyStr("trash"))
    elif random.random() < RANDOM_BAN_THRESHOLD:
        await _ban_helper(ctx, "This is a bad idea and you should feel bad.")
    else:
        await ctx.quote_reply(
            "Thanks for the suggestion! Adding it to the backlog.",
        )
        logging.info("Sending suggestion to /dev/null")
