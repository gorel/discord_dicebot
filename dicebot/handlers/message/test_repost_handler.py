#!/usr/bin/env python3

from unittest.mock import AsyncMock, patch

from dicebot.handlers.message.repost_handler import RepostHandler
from dicebot.data.db.pun import Pun
from dicebot.commands.ask import AskOpenAI
from dicebot.test.utils import TestMessageContext, DicebotTestCase


class TestRepostHandler(DicebotTestCase):
    async def test_handle_parameterized(self):
        handler = RepostHandler()
        scenarios = [
            # new pun: no existing entry -> record and no ban
            ("A ||p1|| extra", None, "", True, False),
            # existing pun, AI says no -> no record update, no ban
            ("B ||p2|| extra", Pun(guild_id=1, setup="X", punchline="p2", first_poster_id=2), "no", False, False),
            # existing pun, AI says yes -> ban (no new record)
            ("C ||p3|| extra", Pun(guild_id=1, setup="Y", punchline="p3", first_poster_id=3), "yes", False, True),
        ]
        for content, existing, ai_resp, expect_add, expect_ban in scenarios:
            with self.subTest(content=content, existing=existing, ai_resp=ai_resp):
                ctx = TestMessageContext.get(content)
                # Prepare mocks
                mock_get = AsyncMock(return_value=existing)
                mock_add = AsyncMock()
                mock_ask = AsyncMock(return_value=ai_resp)
                mock_ban = AsyncMock()

                # Patch methods
                with patch.object(Pun, 'get_by_punchline', new=mock_get), \
                     patch.object(Pun, 'add_or_get', new=mock_add), \
                     patch.object(AskOpenAI, 'ask', new=mock_ask), \
                     patch('dicebot.handlers.message.repost_handler.ban_internal', new=mock_ban):
                    # Ensure quote_reply and fetch_user exist
                    ctx.quote_reply = AsyncMock()
                    ctx.client.fetch_user = AsyncMock(return_value=AsyncMock(name='User'))
                    await handler.handle(ctx)

                # Assert get_by_punchline always invoked
                mock_get.assert_awaited_once_with(ctx.session, ctx.guild_id, content.split('||')[1].strip())
                # Assert add_or_get called only when expected
                if expect_add:
                    mock_add.assert_awaited_once()
                else:
                    self.assertFalse(mock_add.called)
                # Assert ban_internal called only when expected
                if expect_ban:
                    mock_ban.assert_awaited_once()
                    # Also quote_reply should have been called
                    ctx.quote_reply.assert_awaited()
                else:
                    self.assertFalse(mock_ban.called)