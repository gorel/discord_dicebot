#!/usr/bin/env python3

import random

import discord


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
            "snollygoster",
            "tallowcatch",
            "wanker",
        ]
    )


def is_admin(user: discord.Member) -> bool:
    is_owner = user.top_role.guild.owner == user
    is_diceboss = has_diceboss_role(user)
    return is_owner or is_diceboss


def has_diceboss_role(user: discord.Member) -> bool:
    diceboss_rolename = "diceboss"
    return any(role.name == diceboss_rolename for role in user.roles)
