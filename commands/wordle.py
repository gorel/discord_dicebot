#!/usr/bin/env python3

import asyncio
import collections
import logging

from message_context import MessageContext


WORDLE_LEN = 5
GREEN_SQUARE = "🟩"
YELLOW_SQUARE = "🟨"
BLACK_SQUARE = "⬛"


async def start_wordle(ctx: MessageContext) -> None:
    """Start a new wordle game"""
    # TODO - create wordle for this player
    wordle = ctx.server_ctx.gen_new_wordle()
    logging.info(f"New Wordle for ctx {ctx.server_ctx.guild_id}: {wordle}")
    await ctx.channel.send(
        "Let's play wordle! Provide your guess with `!wordle <guess>`"
    )


async def wordle(ctx: MessageContext, guess: str) -> None:
    """Play wordle"""
    if guess == "new":
        await start_wordle(ctx)
    elif guess == "reveal":
        wordle = ctx.server_ctx.get_wordle()
        await ctx.channel.send(f"The word is {wordle}")
    elif len(guess) != WORDLE_LEN:
        await ctx.channel.send(f"Guess must be of length {WORDLE_LEN}")
    else:
        # TODO - look up wordle for this player
        wordle = ctx.server_ctx.get_wordle()
        response = []
        char_counts = collections.Counter(wordle)

        for expected, given in zip(wordle, guess):
            if expected == given:
                response.append(GREEN_SQUARE)
                # Count this one as seen
                char_counts[expected] -= 1
            else:
                # We cover yellow squares later
                response.append(BLACK_SQUARE)

        # We loop once more to check for out of place chars
        for i, given in enumerate(guess):
            if char_counts.get(given, 0) > 0:
                response[i] = YELLOW_SQUARE
                # Reduce the char_counts here because (for example) if the
                # solution is BAAAB and the user guesses ABAAA, we want to
                # show [Y][Y][G][G][B], not [Y][Y][G][G][Y] because at the
                # last letter, we would have "used" all A letters already.
                char_counts[given] -= 1

        await ctx.channel.send("".join(response))
