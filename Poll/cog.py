from discord.ext.commands import (
    Bot,
    Cog,
    Context,

    group
)

class Poll(Cog):
    def __init__(self, bot: Bot):
        pass

    @group(name='poll')
    async def poll_group(self, ctx: Context):
        pass

    @poll_group.command(name='test')
    async def poll_test(self, ctx: Context):
        await ctx.send("aaa")