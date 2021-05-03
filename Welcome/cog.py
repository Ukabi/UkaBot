############################################# IMPORTS #############################################

#################### DISCORD ####################
from discord import (
    Embed,
    Member,
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

##################### DATA ######################
from .data import Guild as GuildData

##################### UTILS #####################
from typing import Union
from utils import Config as Cfg
from utils.checks import admin
from utils.exceptions import InvalidArguments

############################################## COGS ###############################################

class Welcome(Cog):

    ######################################### CONSTRUCTOR #########################################

    def __init__(self, bot: Bot):
        self.config = Cfg(self)

        defaults = GuildData(
            channel=0,
            title="Welcome!",
            message="Welcome to the server {0.mention}!"
        )
        self.config.defaults_guild(defaults)

    ########################################### EVENTS ############################################

    @Cog.listener()
    async def on_member_join(self, member: Member):
        guild = member.guild

        # GuildData
        guild_data = self.config.guild(guild).get()

        channel_id = guild_data.channel
        channel = guild.get_channel(channel_id)

        if channel:
            title = guild_data.title
            message  = guild_data.message
            embed = Embed(
                title=title.format(member),
                description=message.format(member)
            )

            await channel.send(embed=embed)

    ###################################### WELCOME COMMANDS #######################################

    @admin()
    @group()
    async def welcome(self, ctx: Context):
        pass

    @admin()
    @welcome.command()
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

    @admin()
    @welcome.command()
    async def message(self, ctx: Context, *, message: str):
        guild_config = self.config.guild(ctx.guild)
        guild_data = guild_config.get()

        guild_data.message = message
        guild_config.set(guild_data)

        embed = Embed(
            title='Message Changed',
            description=(
                'Successfully updated welcome message to :\n' +
                message
            )
        )
        await ctx.send(embed=embed)

    @admin()
    @welcome.command()
    async def title(self, ctx: Context, *, title: str):
        guild_config = self.config.guild(ctx.guild)
        guild_data = guild_config.get()

        guild_data.title = title
        guild_config.set(guild_data)

        embed = Embed(
            title='Message Changed',
            description=f'Successfully updated welcome message to {title}'
        )
        await ctx.send(embed=embed)