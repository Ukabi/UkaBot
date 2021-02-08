############################################# IMPORTS #############################################

#################### DISCORD ####################
from discord import (
    Embed,
    TextChannel
)
from discord.ext.commands import (
    BadArgument,
    Bot,
    Cog,
    Context,
    TextChannelConverter,
)
from discord.ext.commands import group

##################### UTILS #####################
from typing import Union
from utils import Config as Cfg
from utils import (
    admin,
    update_config
)
from utils.exceptions import InvalidArguments

############################################### COGS ##############################################

class Poll(Cog):
    FIGURES = {n: f'{n}\u20e3' for n in range(1, 10)}
    SEP = '|'

    CHANNEL = 'channel'

    ######################################### CONSTRUCTOR #########################################

    def __init__(self, bot: Bot):
        self.config = Cfg(self)

        defaults = {
            self.CHANNEL: 0
        }
        self.config.defaults_guild(defaults)

    ######################################## POLL COMMANDS ########################################

    @admin()
    @group(name='poll')
    async def poll_group(self, ctx: Context):
        pass

    @admin()
    @poll_group.command(name='create')
    async def poll_create(self, ctx: Context, *, args: str):
        """**[question] | [proposition] | [proposition] | ... ** :
        submits a poll to precised channel.
        """
        args = [arg.strip() for arg in args.split(sep=self.SEP)]

        question = args.pop(0)
        answers_list = [f'{self.FIGURES[n+1]}: {p}' for n, p in enumerate(args)]
        answers = "\n\n".join(answers_list)

        if len(answers_list) in range(2, 10):
            guild = ctx.guild
            guild_data = self.config.guild(guild).get()

            channel = guild.get_channel(guild_data[self.CHANNEL])
            if channel:
                embed = Embed(
                    title=question,
                    description=answers
                )
                message = await channel.send(embed=embed)
                for n in range(1, len(answers_list) + 1):
                    await message.add_reaction(self.FIGURES[n])

                embed = Embed(
                    title='Poll sent',
                    description=f'Poll successfully sent to {channel.mention}'
                )
                await ctx.send(embed=embed)

            else:
                error = InvalidArguments(
                    ctx,
                    title='Channel Error',
                    message='Channel not found or not provided'
                )
                await error.execute()

        else:
            error = InvalidArguments(
                ctx,
                message="Arguments couldn't be parsed"
            )
            await error.execute()

    @admin()
    @poll_group.command(name='channel')
    async def poll_channel(self, ctx: Context,
                           channel: Union[TextChannel, str, int]):
        """
        **[#channel or channel name]** :
        sets the channel where to send polls.
        """
        try:
            if not isinstance(channel, TextChannel):
                channel = await TextChannelConverter().convert(ctx, str(channel))

            update_config(
                config=self.config.guild(ctx.guild),
                attribute=self.CHANNEL,
                value=channel.id
            )

            embed = Embed(
                title='Channel Changed',
                description=f'Successfully updated channel to {channel.mention}'
            )
            await ctx.send(embed=embed)

        except BadArgument:
            error = InvalidArguments(
                ctx,
                title='Channel Error',
                message='Channel not found or not provided'
            )
            await error.execute()