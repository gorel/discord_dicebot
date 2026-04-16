#!/usr/bin/env python3

from unittest.mock import AsyncMock, create_autospec, patch

from dicebot.commands import rep as rep_cmd
from dicebot.data.db.rep import Rep
from dicebot.data.db.user import User
from dicebot.test.utils import DicebotTestCase, TestMessageContext


class TestRep(DicebotTestCase):
    @patch("dicebot.commands.rep.Rep.give", new_callable=AsyncMock)
    @patch("dicebot.commands.rep.Rep.get_total_received", new_callable=AsyncMock)
    async def test_rep_success(self, mock_total, mock_give):
        ctx = TestMessageContext.get()
        ctx.author.id = 1
        target = create_autospec(User)
        target.id = 2
        target.as_mention.return_value = "<@2>"
        mock_give.return_value = None
        mock_total.return_value = 15
        await rep_cmd.rep(ctx, 5, target)
        mock_give.assert_awaited_once_with(
            ctx.session, guild_id=ctx.guild_id, giver_id=1, receiver_id=2, amount=5
        )
        ctx.channel.send.assert_awaited_once()
        msg = ctx.channel.send.call_args[0][0]
        assert "+5" in msg
        assert "15" in msg or "+15" in msg

    async def test_rep_self(self):
        ctx = TestMessageContext.get()
        target = create_autospec(User)
        target.id = ctx.author_id  # same as author
        await rep_cmd.rep(ctx, 5, target)
        ctx.channel.send.assert_awaited_once()
        msg = ctx.channel.send.call_args[0][0]
        assert "can't rep yourself" in msg.lower()
        ctx.session.add.assert_not_called()
