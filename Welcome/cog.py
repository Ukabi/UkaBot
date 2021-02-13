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

##################### UTILS #####################
from typing import Union
from utils import Config as Cfg
from utils import (
    admin,
    update_config
)
from utils.exceptions import InvalidArguments

############################################## COGS ###############################################

class Welcome(Cog):
    TITLE = 'title'
    MESSAGE = 'message'
    CHANNEL = 'channel'

    ###############################################################################################

    def __init__(self, bot: Bot):
        defaults = {
            self.CHANNEL: 0,
            self.TITLE: "Welcome!",
            self.MESSAGE: "Welcome to the server {0.mention}!"
        }
        self.config = Cfg(self, defaults=defaults)

    ########################################### EVENTS ############################################

    @Cog.listener()
    async def on_member_join(self, member: Member):
        guild = member.guild
        guild_data = self.config.guild(guild).get()

        channel_id = guild_data[self.CHANNEL]
        channel = guild.get_channel(channel_id)

        if channel:
            title = guild_data[self.TITLE]
            message  = guild_data[self.MESSAGE]
            embed = Embed(
                title=title.format(member),
                description=message.format(member)
            )

            await channel.send(embed=embed)

    ###################################### WELCOME COMMANDS #######################################

    @admin()
    @group(name='welcome')
    async def welcome_group(self, ctx: Context):
        pass

    @admin()
    @welcome_group.command(name='channel')
    async def welcome_channel(
        self, ctx: Context, channel: Union[TextChannel, str, int]
    ):
        """**[#channel or channel name]** :
        sets the channel where to send messages.
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
                ctx=ctx,
                title='Channel Error',
                message='Channel not found or not provided'
            )
            await error.execute()

    @admin()
    @welcome_group.command(name='message')
    async def welcome_message(self, ctx: Context, *, message: str):
        """**[message]** : edits the welcome message's text."""
        update_config(
            config=self.config.guild(ctx.guild),
            attribute=self.MESSAGE,
            value=message
        )

    @admin()
    @welcome_group.command(name='title')
    async def welcome_title(self, ctx: Context, *, title: str):
        """**[text]** : edits the welcome message's title."""
        update_config(
            config=self.config.guild(ctx.guild),
            attribute=self.TITLE,
            value=title
        )