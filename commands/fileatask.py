#!/usr/bin/env python3

import logging
import os
import asyncio
import random
import requests
import time

from commands import ban
from message_context import MessageContext
from models import DiscordUser, GreedyStr, Time

ISSUES_URL = "https://api.github.com/repos/gorel/discord_dicebot/issues"
SUCCESS_CODE = 201

RANDOM_BAN_THRESHOLD = 0.20


async def _ban_helper(ctx: MessageContext, ban_message: str) -> None:
    await ctx.channel.send(
        ban_message,
        reference=ctx.message,
    )
    await asyncio.sleep(3)
    await ban.ban(
        ctx,
        target=DiscordUser(ctx.message.author.id),
        timer=Time("1hr"),
        ban_as_bot=True,
    )


async def fileatask(ctx: MessageContext, title: GreedyStr) -> None:
    """pretend to fileatask because authentication is hard"""

    # TODO: if message author is gorel, call _fileatask_real

    if "fix" in title.split():
        await _ban_helper(
            ctx,
            "I'm not fixing this for you heathens.",
        )
    elif random.random() < RANDOM_BAN_THRESHOLD:
        await _ban_helper(
            ctx,
            "This is a bad idea and you should feel bad.",
        )
    elif ctx.server_ctx.bans.get(ctx.message.author.id, -1) > time.time():
        await ctx.channel.send("Your opinion does not matter.", reference=ctx.message)
    else:
        await ctx.channel.send(
            "Thanks for the suggestion! Adding it to the backlog.",
            reference=ctx.message,
        )
        logging.info("Sending suggestion to /dev/null")


async def _fileatask_real(ctx: MessageContext, title: GreedyStr) -> None:
    """Add a new issue to the github repository"""
    headers = {"accept": "application/vnd.github+json"}
    user = os.getenv("GITHUB_USER") or ""
    password = os.getenv("GITHUB_PASS") or ""
    r = requests.post(
        ISSUES_URL, json={"title": title}, headers=headers, auth=(user, password)
    )
    if r.status_code == SUCCESS_CODE:
        response_url = r.json()["html_url"]
        await ctx.channel.send(f"Your suggestion has been noted: {response_url}")
    else:
        logging.error(f"Request to GitHub failed: {r.json()}")
        await ctx.channel.send(
            "Something went wrong submitting the issue to GitHub (status_code = {r.status_code})"
        )
