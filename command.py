#!/usr/bin/env python3

import random

import discord

import db_helper
from message_context import MessageContext


def get_witty_insult() -> str:
    return random.choice(
        [
            "bucko",
            "bud",
            "glue eater",
            "kid",
            "ninny",
            "pal",
            "scrub",
            "son",
            "wanker",
            "bitch",
            "buddy",
            "libtard",
            "autist",
            "bonehead",
            "jackass",
            "asshole",
            "mouthbreather",
            "you fucker",
            "whore",
            "cocksucker",
            "dick",
            "piece of shit weeb",
            "fuck face",
            "goober",
            "donkey",
            "Gayboy Advanced"
            "dildo",
            "douche canoe",
            "fuckface",
        ]
    )


def has_diceboss_role(user: discord.Member) -> bool:
    diceboss_rolename = "diceboss"
    return any(role.name == diceboss_rolename for role in user.roles)
