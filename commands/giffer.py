#!/usr/bin/env python3

import json
import os
import random
import requests
from typing import List, Optional

from message_context import MessageContext
from models import GreedyStr

class TenorGifRetriever:
    def __init__(self, api_key: Optional[str] = None) -> None:
        self.api_key = api_key or os.getenv("TENOR_API_KEY")

    def get(self, q: str) -> List[str]:
        url = "https://g.tenor.com/v1/search"
        params = {
            "q": q,
            "key": self.api_key,
            "locale": "en_US",
            "content_filter": "low",
        }
        try:
            response = requests.get(url, params=params)
            top_gifs = json.loads(response.content)["results"]
            return [gif["url"] for gif in top_gifs]
        except Exception:
            return []


async def gif(ctx: MessageContext, q: GreedyStr) -> None:
    """Retrieve a random GIF from Tenor when searching the query string"""
    retriever = TenorGifRetriever()
    urls = retriever.get(q)
    if len(urls) == 0:
        logging.warning(f"Could not find any GIFs for query {q}")
        await ctx.channel.send("Could not find any GIFs for that query :(")
    else:
        choice = random.choice(urls)
        logging.info(f"Sending GIF {choice}")
        await ctx.channel.send(choice)
