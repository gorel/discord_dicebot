#!/usr/bin/env python3

import logging
import os

import requests

import command
from message_context import MessageContext
from models import GreedyStr

ISSUES_URL = "https://api.github.com/repos/gorel/discord_dicebot/issues"
SUCCESS_CODE = 201


async def fileatask(ctx: MessageContext, title: GreedyStr) -> None:
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
