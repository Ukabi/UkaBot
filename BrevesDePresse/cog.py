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

        self.default_guild = GuildData([])
        self.config.defaults_guild(self.default_guild)

    ############################################ EVENTS ###########################################

    async def treat_message(self, message: Message, *, message_post: bool):
        guild = message.guild

        if message.channel.id not in (filter_ := self.config.guild(guild).get().channels):
            return
        
        if message.author.bot:
            return

        if message_post:
            thread = await message.create_thread(
                name=self.__get_thread_title(message),
                auto_archive_duration=60 # limiting visibility to one hour
            )

            if thread.name.startswith("http"):
                await asyncio.sleep(1)
                message = await message.fetch() # refreshing message waiting for an embed to parse
                await thread.edit(name=self.__get_thread_title(message))

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

    @admin_or_permissions()
    @bdp_group.group(name='channel')
    async def bdp_channel_group(self, ctx: Context):
        pass

    @admin_or_permissions()
    @bdp_channel_group.command(name='add')
    async def bdp_channel_add(self, ctx: Context, channel: TextChannel):
        config = self.config.guild(ctx.guild)
        data = set(config.get().channels)
        data.add(channel.id)
        config.set(GuildData(list(data)))

        await ctx.message.add_reaction('✅')

    @admin_or_permissions()
    @bdp_channel_group.command(name='remove')
    async def bdp_channel_remove(self, ctx: Context, channel: TextChannel):
        config = self.config.guild(ctx.guild)
        data = set(config.get().channels)
        data.remove(channel.id)
        config.set(GuildData(list(data)))

        await ctx.message.add_reaction('✅')

    ########################################### PRIVATE ###########################################

    @staticmethod
    def __get_thread_title(message: Message) -> str:
        if (embeds := message.embeds):
            embed = embeds[0]
            title, desc = embed.title, embed.description
            name = f'{title if title else ""}{desc if desc else ""}'

        else: # no embed case
            name = message.content

        name = name[:100] # limiting name size to avoid being prohibited
        name = name if name else "No Title" # avoiding empty names (eg: picture only)

        return name
