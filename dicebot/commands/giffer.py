#!/usr/bin/env python3

import logging
import os
import random
from typing import List, Optional

import aiohttp

from dicebot.data.message_context import MessageContext
from dicebot.data.types.greedy_str import GreedyStr


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


async def gif(ctx: MessageContext, q: GreedyStr) -> None:
    """Retrieve a random GIF from Tenor when searching the query string"""
    retriever = TenorGifRetriever()
    urls = await retriever.get(q)
    if len(urls) == 0:
        logging.warning(f"Could not find any GIFs for query {q}")
        await ctx.channel.send("Could not find any GIFs for that query :(")
    else:
        choice = random.choice(urls)
        logging.info(f"Sending GIF {choice}")
        await ctx.channel.send(choice)
