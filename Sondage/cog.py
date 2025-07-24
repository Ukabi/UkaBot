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

class Sondage(Cog):

    ######################################### CONSTRUCTOR #########################################

    def __init__(self, bot: Bot):
        self.bot = bot
        self.config = Cfg(self)

        self.default_guild = GuildData([], 0)
        self.config.defaults_guild(self.default_guild)

    ############################################ EVENTS ###########################################

    async def treat_message(self, message: Message, *, message_post: bool):
        guild = message.guild

        if message.channel.id not in (config := self.config.guild(guild).get()).channels:
            return
        
        if message.author.bot:
            return

        if message_post and (poll := message.poll):
            thread = await message.create_thread(
                name=p if (p := poll.question[:100]) else "No Title"
            )
        
        elif message_post and not poll:
            dm = await message.author.create_dm()
            await dm.send(
                f"Seuls les sondages sont autorisés sur le cannal {message.channel}.\n"
                "Veuillez discuter sur un des fils dédiés."
            )

            log = guild.get_channel(config.log)
            m = f"Sondage - Message de {message.author} supprimé dans {message.channel}."
            if log:
                await log.send(m)
            print(m)

            await message.delete()

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
    @group(name='sondage')
    async def sondage_group(self, ctx: Context):
        pass

    @admin_or_permissions()
    @sondage_group.group(name='channel')
    async def sondage_channel_group(self, ctx: Context):
        pass

    @admin_or_permissions()
    @sondage_channel_group.command(name='add')
    async def bdp_channel_add(self, ctx: Context, channel: TextChannel):
        config = self.config.guild(ctx.guild)

        data = config.get()
        channels = set(data.channels)

        channels.add(channel.id)

        data.channels = list(channels)
        config.set(data)

        await ctx.message.add_reaction('✅')

    @admin_or_permissions()
    @sondage_channel_group.command(name='remove')
    async def bdp_channel_remove(self, ctx: Context, channel: TextChannel):
        config = self.config.guild(ctx.guild)

        data = config.get()
        channels = set(data.channels)

        channels.remove(channel.id)

        data.channels = list(channels)
        config.set(data)

        await ctx.message.add_reaction('✅')
    
    @admin_or_permissions()
    @sondage_group.command(name='log')
    async def sondage_log(self, ctx: Context, channel: TextChannel):
        config = self.config.guild(ctx.guild)
        data = config.get()
        data.log = channel.id
        config.set(data)

        await ctx.message.add_reaction('✅')
