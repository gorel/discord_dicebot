#!/usr/bin/env python3

import logging
import os
import random
from typing import List, Optional

import aiohttp

from dicebot.core.register_command import register_command
from dicebot.data.types.greedy_str import GreedyStr
from dicebot.data.types.message_context import MessageContext


class TenorGifRetriever:
    def __init__(self, api_key: Optional[str] = None) -> None:
        self.api_key = api_key or os.getenv("TENOR_API_KEY")

    async def get(self, q: str) -> List[str]:
        url = "https://g.tenor.com/v1/search"
        params = {
            "q": q,
            "key": self.api_key,
            "locale": "en_US",
            "content_filter": "low",
            "media_filter": "basic",
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    json_resp = await response.json()
                    top_gifs = json_resp["results"]
                    return [gif["url"] for gif in top_gifs]
        except Exception:
            return []


async def get_random_gif_url(q: str) -> Optional[str]:
    retriever = TenorGifRetriever()
    urls = await retriever.get(q)
    if len(urls) == 0:
        logging.warning(f"Could not find any GIFs for query {q}")
        return None
    else:
        return random.choice(urls)


@register_command
async def gif(ctx: MessageContext, q: GreedyStr) -> None:
    """Retrieve a random GIF from Tenor when searching the query string"""
    q_str = q.unwrap()
    url = await get_random_gif_url(q_str)
    if url is None:
        logging.warning(f"Could not find any GIFs for query {q_str}")
        await ctx.send("Could not find any GIFs for that query :(")
    else:
        logging.info(f"Sending GIF {url}")
        await ctx.send(url)
