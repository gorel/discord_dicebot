#!/usr/bin/env python3

import asyncio
import logging

import pytube

from data_infra.message_context import MessageContext
from on_message_handlers.abstract_handler import AbstractHandler

YOUTUBE_TRIGGERS = ["youtube.com", "youtu.be"]
VIDEO_LENGTH_COMPLAINT_THRESHOLD_MINUTES = 10


class YoutubeHandler(AbstractHandler):
    """Easter egg for long YouTube videos"""

    def __init__(self) -> None:
        self.video_length_mins = 0

    async def should_handle(
        self,
        ctx: MessageContext,
    ) -> bool:
        for embed in ctx.message.embeds:
            if embed.url is not None and any(
                yt_trigger in embed.url.lower() for yt_trigger in YOUTUBE_TRIGGERS
            ):
                self.video_length_mins = 0
                try:
                    video = pytube.YouTube(embed.url)
                    self.video_length_mins = video.length // 60
                    logging.info(f"Found video of length {self.video_length_mins} mins")
                except Exception as e:
                    logging.warning(
                        f"Failed to get YouTube info for `{embed.url}`: {e}"
                    )
                    continue

                # If the video isn't too long, don't handle it (but keep checking other embeds)
                if self.video_length_mins > VIDEO_LENGTH_COMPLAINT_THRESHOLD_MINUTES:
                    return True
        # No embeds had a long YT video
        return False

    async def handle(
        self,
        ctx: MessageContext,
    ) -> None:
        await ctx.channel.send(
            f"{self.video_length_mins} minutes?", reference=ctx.message
        )
        await asyncio.sleep(1)
        await ctx.channel.send("Bro, I don't have time to watch this")
