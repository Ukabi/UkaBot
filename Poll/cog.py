############################################# IMPORTS #############################################

#################### DISCORD ####################
from discord import (
    Embed,
    TextChannel
)
from discord.ext.commands import (
    Bot,
    Cog,
    Context,
    TextChannelConverter,
)
from discord.ext.commands import group
from discord.ext.commands import BadArgument

##################### DATA ######################
from .data import Guild as GuildData
from .data import (
    FIGURES,
    SEP
)

##################### UTILS #####################
from typing import Union
from utils import Config as Cfg
from utils.checks import admin
from utils.exceptions import InvalidArguments

############################################### COGS ##############################################

class Poll(Cog):

    ######################################### CONSTRUCTOR #########################################

    def __init__(self, bot: Bot):
        self.config = Cfg(self)

        defaults = GuildData(channel=0)
        self.config.defaults_guild(defaults)

    ######################################## POLL COMMANDS ########################################

    @admin()
    @group()
    async def poll(self, ctx: Context):
        pass

    @admin()
    @poll.command()
    async def create(self, ctx: Context, *, args: str):
        try:
            args = [arg.strip() for arg in args.split(sep=SEP)]

            question = args.pop(0)

            if len(args) in range(1, 10):
                guild = ctx.guild

                # Dict[int, GuildData]
                guild_data = self.config.guild(guild).get()

                answers_list = [f'{self.FIGURES[n+1]}: {p}' for n, p in enumerate(args)]
                answers = "\n\n".join(answers_list)

                channel = guild.get_channel(guild_data.channel)
                if channel:
                    embed = Embed(
                        title=question,
                        description=answers
                    )
                    message = await channel.send(embed=embed)
                    for n in range(1, len(answers_list) + 1):
                        await message.add_reaction(FIGURES[n])

                    embed = Embed(
                        title='Poll sent',
                        description=f'Poll successfully sent to {channel.mention}'
                    )
                    await ctx.send(embed=embed)

                else:
                    raise InvalidArguments(
                        ctx=ctx,
                        title='Channel Error',
                        message='Channel not found or not provided'
                    )

            else:
                raise InvalidArguments(
                    ctx=ctx,
                    message=(
                        "Arguments couldn't be parsed" + "\n"
                        "Check separator or answer count (9 max)"
                    )
                )

        except InvalidArguments as error:
            await error.execute()

    @admin()
    @poll.command()
    async def channel(self, ctx: Context, channel: Union[TextChannel, str, int]):
        try:
            if not isinstance(channel, TextChannel):
                channel = await TextChannelConverter().convert(ctx, str(channel))
        except BadArgument:
            error = InvalidArguments(
                ctx=ctx,
                title='Channel Error',
                message='Channel not found or not provided'
            )
            await error.execute()
            return

        else:
            guild_config = self.config.guild(ctx.guild)
            guild_data = guild_config.get()
            guild_data.channel = channel.id
            guild_config.set(guild_data)

            embed = Embed(
                title='Channel Changed',
                description=f'Successfully updated channel to {channel.mention}'
            )
            await ctx.send(embed=embed)
