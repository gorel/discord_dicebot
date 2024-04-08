#!/usr/bin/env python3

import discord
from MemePy import MemeFactory, MemeGenerator

from dicebot.core.register_command import register_command
from dicebot.data.types.greedy_str import GreedyStr
from dicebot.data.types.message_context import MessageContext


def format_for_list(name: str) -> str:
    meme = MemeFactory.MemeLib[name]
    required_args = meme.count_non_optional()
    optional_args = len(meme.text_zones) - required_args
    return f"{name}: {required_args} required args, {optional_args} optional args"


@register_command
async def meme(ctx: MessageContext, q: GreedyStr) -> None:
    """Generate a meme using MemePy. Type `list` for a list of templates."""
    template_str, *args = q.unwrap_as_args()
    if template_str == "list":
        await ctx.send(
            "\n".join(format_for_list(m) for m in sorted(MemeFactory.MemeLib))
        )
        return

    template = MemeFactory.MemeLib.get(template_str)
    if template is None:
        await ctx.send(f"Unknown template '{template_str}'")
        return

    image_bytes = MemeGenerator.get_meme_image_bytes(template_str, args)
    fmt = template.image_file_path.split(".")[-1]
    await ctx.channel.send(file=discord.File(image_bytes, f"meme.{fmt}"), silent=True)
