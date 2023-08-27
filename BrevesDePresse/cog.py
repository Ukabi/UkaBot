############################################# IMPORTS #############################################

#################### DISCORD ####################
from discord import (
    Message,
    TextChannel
)
from discord.ext.commands import (
    Bot,
    Cog,
    Context
)
from discord.ext.commands import group

##################### DATA ######################
from .data import Guild as GuildData

##################### UTILS #####################
import asyncio
from utils import Config as Cfg
from utils.checks import admin_or_permissions


############################################### COGS ##############################################

class BrevesDePresse(Cog):

    ######################################### CONSTRUCTOR #########################################

    def __init__(self, bot: Bot):
        self.bot = bot
        self.config = Cfg(self)

        self.default_guild = GuildData(0)
        self.config.defaults_guild(self.default_guild)

    ############################################ EVENTS ###########################################

    async def treat_message(self, message: Message, *, message_post: bool):
        guild = message.guild

        if message.channel.id != (filter_ := self.config.guild(guild).get().channel):
            return
        
        if message.author.bot:
            return

        if message_post: # message post case
            if (embeds := message.embeds):
                embed = embeds[0]
                name = f"{embed.title}{embed.description}"
            else:
                name = message.content

            thread = await message.create_thread(
                name=name[:100], # limiting name size to avoid being prohibited
                auto_archive_duration=60 # limiting visibility to one hour
            )

        else: # message delete case
            thread = guild.get_channel_or_thread(message.id)
            if thread:
                await thread.delete()

    @Cog.listener()
    async def on_message(self, message: Message):
        await self.treat_message(message, message_post=True)

    @Cog.listener()
    async def on_message_delete(self, message: Message):
        await self.treat_message(message, message_post=False)

    ########################################### COMMANDS ##########################################

    @admin_or_permissions()  # might add other perms than just admin
    @group(name='bdp')
    async def bdp_group(self, ctx: Context):
        pass

    @admin_or_permissions()  # might add other perms than just admin
    @bdp_group.command(name='channel')
    async def rava_channel(self, ctx: Context, channel: TextChannel):
        self.config.guild(ctx.guild).set(GuildData(channel.id))
        await ctx.message.add_reaction('✅')
