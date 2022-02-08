#!/usr/bin/env python3

import asyncio
import logging
import os
import pathlib

import discord

from message_context import MessageContext


async def audio(ctx: MessageContext, name: str) -> None:
    """Play an audio file (must be known by the bot already)"""
    # Can't put this in a global since load_dotenv needs to be called first
    dirname = pathlib.Path(os.getenv("AUDIO_DIR"))
    path = (dirname / name).with_suffix(".opus")
    if not path.is_file():
        await ctx.channel.send(f"Could not find audio file {path}")
    else:
        logging.info(f"Trying to play file {path}")
        # Grab the correct audio channel
        audio_channel = ctx.message.author.voice.channel
        # If we couldn't find the audio channel, bail now
        if audio_channel is None:
            await ctx.channel.send(
                "Join an audio channel first to use the !audio command"
            )
        else:
            logging.info(f"Playing audio in channel {audio_channel.name}")
            audio_source = await discord.FFmpegOpusAudio.from_probe(path)
            voice_client = await audio_channel.connect()
            voice_client.play(audio_source)
            while voice_client.is_playing():
                await asyncio.sleep(0.5)
            logging.info(f"Done sending audio to {audio_channel.name}")
            await voice_client.disconnect()
