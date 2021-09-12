#!/usr/bin/env python3

import random

import discord

import db_helper
from message_context import MessageContext


def get_witty_insult() -> str:
    return random.choice(
        [
            "bucko",
            "cumberworld",
            "dunderhead",
            "fopdoodle",
            "glue eater",
            "kid",
            "lubberwort",
            "mouthbreather",
            "ninny",
            "pal",
            "quisby",
            "rascal",
            "scrub",
            "tallowcatch",
            "wanker",
        ]
    )


def has_diceboss_role(user: discord.Member) -> bool:
    diceboss_rolename = "diceboss"
    return any(role.name == diceboss_rolename for role in user.roles)
