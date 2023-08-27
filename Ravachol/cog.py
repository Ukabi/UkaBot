############################################# IMPORTS #############################################

#################### DISCORD ####################
from discord import Message
from discord.ext.commands import (
    Bot,
    Cog,
    Context
)
from discord.ext.commands import group

##################### DATA ######################
from .data import (
    Event,
    Guild as GuildData
)

##################### UTILS #####################
from typing import List
from utils import (
    Config as Cfg,
    ImprovedList
)
from utils.checks import admin_or_permissions


############################################### COGS ##############################################

class Ravachol(Cog):

    ######################################### CONSTRUCTOR #########################################

    def __init__(self, bot: Bot):
        self.bot = bot
        self.config = Cfg(self)

        self.default_guild = GuildData(events=[])
        self.config.defaults_guild(self.default_guild)

    ############################################ EVENTS ###########################################

    async def treat_message(self, message: Message):
        guild = message.guild
        if not guild:
            return

        guild_config = self.config.guild(guild)
        guild_data = guild_config.get()

        to_treat: List[Event] = filter(lambda e: e.filter(message, self.bot), guild_data.events)
        to_reply: List[str] = map(lambda e: e.get(), to_treat)

        channel = message.channel
        for reply in to_reply:
            await channel.send(reply)

    @Cog.listener()
    async def on_message(self, message: Message):
        await self.treat_message(message)

    ########################################### COMMANDS ##########################################

    @admin_or_permissions()  # might add other perms than just admin
    @group(name='rava')
    async def rava_group(self, ctx: Context):
        pass

    @admin_or_permissions()  # might add other perms than just admin
    @rava_group.command(name='add')
    async def rava_add(self, ctx: Context, frequency: float, trigger: str, *, content: str):
        guild = ctx.guild
        if not guild:
            return  # might implement proper error reply

        frequency = float(frequency)
        if frequency > 1 or frequency <= 0:
            return  # might implement proper error reply

        guild_config = self.config.guild(guild)
        guild_data = guild_config.get()

        event = Event(
            frequency=frequency,
            trigger=trigger,
            content=[c.strip() for c in content.split('|')]
        )
        guild_data.events.append(event)
        guild_config.set(guild_data)

    @admin_or_permissions()
    @rava_group.command(name='remove')
    async def rava_remove(self, ctx: Context, *, trigger: str):
        guild = ctx.guild
        if not guild:
            return  # might implement proper error reply

        guild_config = self.config.guild(guild)
        guild_data = guild_config.get()

        events = ImprovedList(guild_data.events)
        try:
            events.remove(trigger, key=lambda e: e.trigger)
        except ValueError:
            return  # might implement proper error reply

        guild_data.events = events
        guild_config.set(guild_data)

        await ctx.message.add_reaction('✅')
