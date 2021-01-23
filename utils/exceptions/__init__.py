############################################# IMPORTS #############################################

from discord import Embed
from discord.ext.commands import Context

############################################# CLASSES #############################################

class BaseDiscordException:
    def __init__(
        self,
        ctx: Context,
        title: str = 'Error',
        message: str = '',
        color: int = 0xFF0000
    ):
        self.ctx = ctx
        self.title = title
        self.message = message
        self.color = color

    async def execute(self):
        await self.ctx.send(
            Embed(
                color=self.color,
                title=self.title,
                description=self.message
            )
        )

class InvalidArguments(BaseDiscordException):
    def __init__(
        self,
        ctx: Context,
        title: str = 'Invalid Arguments',
        message: str = '',
        color: int = 0xFF0000
    ):
        super().__init__(
            ctx,
            title,
            message,
            color
        )

class CommandNotFound(BaseDiscordException):
    def __init__(
        self,
        ctx: Context,
        title: str = 'Command Not Found',
        message: str = '',
        color: int = 0xFF0000
    ):
        super().__init__(
            ctx,
            title,
            message,
            color
        )