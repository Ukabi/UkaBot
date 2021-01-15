from discord.ext.commands import (
    Bot,
    Cog,
    Context,

    group
)

class Birthday(Cog):
    def __init__(self, bot: Bot):
        pass

    @group(name='birthday')
    async def birthday_group(self, ctx: Context):
        pass

    @birthday_group.command(name='test')
    async def birthday_test(self, ctx: Context):
        await ctx.send("aaa")