#!/usr/bin/env python3

from dataclasses import dataclass
from unittest.mock import AsyncMock, patch

from dicebot.data.types import state_keys
from dicebot.handlers.message.repost_handler import RepostHandler
from dicebot.data.db.pun import Pun
from dicebot.commands.ask import AskOpenAI
from dicebot.test.utils import TestMessageContext, DicebotTestCase


class TestRepostHandler(DicebotTestCase):
    @dataclass
    class Scenario:
        content: str
        existing: Pun | None = None
        ai_response: str = ""
        expect_add: bool = False
        expect_ban: bool = False

    async def test_handle_parameterized(self):
        handler = RepostHandler()
        testcases = [
            # new pun: no existing entry -> record and no ban
            TestRepostHandler.Scenario(content="A ||p1|| extra", expect_add=True),
            # existing pun, AI says no -> no record update, no ban
            TestRepostHandler.Scenario(
                content="B ||p2|| extra",
                existing=Pun(guild_id=1, setup="X", punchline="p2", first_poster_id=2),
                ai_response="no",
            ),
            # existing pun, AI says yes -> ban (no new record)
            TestRepostHandler.Scenario(
                content="C ||p3|| extra",
                existing=Pun(guild_id=1, setup="Y", punchline="p3", first_poster_id=3),
                ai_response="yes",
                expect_ban=True,
            ),
        ]
        for tc in testcases:
            with self.subTest(
                content=tc.content,
                existing=tc.existing,
                ai_response=tc.ai_response,
            ):
                ctx = TestMessageContext.get(tc.content)
                ctx.state[state_keys.WAS_PUN] = True
                # Prepare mocks
                mock_get = AsyncMock(return_value=tc.existing)
                mock_add = AsyncMock()
                mock_ask = AsyncMock(return_value=tc.ai_response)
                mock_ban = AsyncMock()

                # Patch methods
                with (
                    patch.object(Pun, "get_by_punchline", new=mock_get),
                    patch.object(Pun, "add_or_get", new=mock_add),
                    patch.object(AskOpenAI, "ask", new=mock_ask),
                    patch(
                        "dicebot.handlers.message.repost_handler.ban_internal",
                        new=mock_ban,
                    ),
                ):
                    # Ensure quote_reply and fetch_user exist
                    ctx.quote_reply = AsyncMock()
                    ctx.client.fetch_user = AsyncMock(
                        return_value=AsyncMock(name="User")
                    )
                    await handler.handle(ctx)

                # Assert get_by_punchline always invoked
                mock_get.assert_awaited_once_with(
                    ctx.session, ctx.guild_id, tc.content.split("||")[1].strip()
                )
                # Assert add_or_get called only when expected
                if tc.expect_add:
                    mock_add.assert_awaited_once()
                else:
                    self.assertFalse(mock_add.called)
                # Assert ban_internal called only when expected
                if tc.expect_ban:
                    mock_ban.assert_awaited_once()
                    # Also quote_reply should have been called
                    ctx.quote_reply.assert_awaited()
                else:
                    self.assertFalse(mock_ban.called)

