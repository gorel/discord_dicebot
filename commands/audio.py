#!/usr/bin/env python3

import pathlib

from message_context import MessageContext


AUDIO_DIR = os.getenv("AUDIO_DIR")


async def audio(ctx: MessageContext, name: str) -> None:
    """Play an audio file (must be known by the bot already)"""
    dirname = pathlib.Path(dirname)
    path = (dirname / name).with_suffix(".opus")
    if not path.is_file():
        await ctx.channel.send(f"Could not find audio file {path}")
    else:
        # Find the correct audio channel
        audio_channel = None
        for channel in ctx.message.guild.voice_channels:
            members = {member.id for member in channel.members}
            if ctx.message.author.id in members:
                audio_channel = channel
                break

        # If we couldn't find the audio channel, bail now
        if audio_channel is None:
            await ctx.channel.send(
                "Join an audio channel first to use the !audio command"
            )
        else:
            await audio_channel.connect()
            with open(path, "rb") as f:
                await audio_channel.send_audio_packet(f.read(), encode=False)
            await audio_channel.disconnect()
