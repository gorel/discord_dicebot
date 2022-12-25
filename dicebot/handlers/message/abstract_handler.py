#!/usr/bin/env python3

import logging
from abc import ABC, abstractmethod

from dicebot.data.types.message_context import MessageContext


class AbstractHandler(ABC):
    @abstractmethod
    async def should_handle(
        self,
        ctx: MessageContext,
    ) -> bool:
        pass

    @abstractmethod
    async def handle(
        self,
        ctx: MessageContext,
    ) -> None:
        pass

    async def should_handle_no_throw(self, ctx: MessageContext) -> bool:
        try:
            return await self.should_handle(ctx)
        except Exception as e:
            logging.exception(
                f"Exception raised in should_handle for {self.__class__.__name__}: {e}"
            )
            return False

    async def handle_no_throw(self, ctx: MessageContext) -> None:
        try:
            await self.handle(ctx)
        except Exception as e:
            logging.exception(
                f"Exception raised in handle for {self.__class__.__name__}: {e}"
            )
