############################################# IMPORTS #############################################

#################### DISCORD ####################
from discord import (
    Embed,
    Member,
    TextChannel
)
from discord.ext.commands import (
    BadArgument,
    Cog,
    Context,
    TextChannelConverter,
)
from discord.ext.commands import (
    group,
    has_guild_permissions,
    has_permissions
)

##################### UTILS #####################
from typing import Union
from utils import Config as Cfg
from utils import update_config

############################################## COGS ###############################################

class Welcome(Cog):
    TITLE = 'title'
    MESSAGE = 'message'
    CHANNEL = 'channel'

    ###############################################################################################

    def __init__(self):
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
    @group(name='welcome')
    async def welcome_group(self, ctx: Context):
        pass

    @admin()
    @welcome_group.command(name='channel')
    async def welcome_channel(self, ctx: Context, channel: Union[TextChannel, str, int]):
        """**[#channel or channel name]** :
        sets the channel where to send messages.
        """
        try:
            if not isinstance(channel, TextChannel):
                channel = await TextChannelConverter().convert(ctx, str(channel))

            update_config(
                ctx=ctx,
                config=self.config.guild(ctx.guild),
                attribute=self.CHANNEL,
                value=channel.id
            )
        except BadArgument:
            pass

    @admin()
    @welcome_group.command(name='message')
    async def welcome_message(self, ctx: Context, *, message: str):
        """**[message]** : edits the welcome message's text."""
        update_config(
            ctx=ctx,
            config=self.config.guild(ctx.guild),
            attribute=self.MESSAGE,
            value=message
        )

    @admin()
    @welcome_group.command(name='title')
    async def welcome_title(self, ctx: Context, *, title: str):
        """**[text]** : edits the welcome message's title."""
        update_config(
            ctx=ctx,
            config=self.config.guild(ctx.guild),
            attribute=self.TITLE,
            value=title
        )