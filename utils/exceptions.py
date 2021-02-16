############################################# IMPORTS #############################################

from discord import Embed
from discord.ext.commands import Context

############################################# CLASSES #############################################

class BaseDiscordException(BaseException):
    def __init__(
        self, ctx: Context = None, title: str = 'Error',
        message: str = '', color: int = 0xFF0000
    ):
        self.ctx = ctx
        self.title = title
        self.message = message
        self.color = color

        print(f"{self.__class__.__name__}: {title}: {message}")

    async def execute(self):
        embed = Embed(
            color=self.color,
            title=self.title,
            description=self.message
        )
        await self.ctx.send(embed=embed)

class InvalidArguments(BaseDiscordException):
    def __init__(
        self, ctx: Context = None, title: str = 'Invalid Arguments',
        message: str = '', color: int = 0xFF0000
    ):
        super().__init__(
            ctx,
            title,
            message,
            color
        )

class CommandNotFound(BaseDiscordException):
    def __init__(
        self, ctx: Context = None, title: str = 'Command Not Found',
        message: str = '', color: int = 0xFF0000
    ):
        super().__init__(
            ctx,
            title,
            message,
            color
        )
