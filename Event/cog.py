############################################# IMPORTS #############################################
#################### DISCORD ####################
from discord import (
    Embed,
    Guild,
    Member,
    TextChannel,
    Role
)

from discord.ext.commands import (
    Bot,
    Cog,
    Context,
    MemberConverter,
    RoleConverter,
    TextChannelConverter
)
from discord.ext.commands import group
from discord.ext.commands import BadArgument

##################### DATA ######################
from .data import (
    Event as EventData,
    Guild as GuildData
)

##################### UTILS #####################
from asyncio import sleep
from datetime import datetime as dt
from typing import Union
from utils import (
    Config as Cfg,
    ImprovedList
)
from utils import lexsorted
from utils.exceptions import InvalidArguments

import time

############################################### COGS ##############################################

class Event(Cog):

    ######################################### CONSTRUCTOR #########################################

    def __init__(self, bot):
        self.bot = bot

        self.config = Cfg(self)

        self.defaults_guild = GuildData(events=[])
        self.config.defaults_guild(self.defaults_guild)

        self.on = True
        self.tasks = []
        self.bot.loop.create_task(self.scheduler())
        print(type(self.bot.loop))
        print("EVENT_COG: loaded")

    ########################################### UNLOADER ##########################################
    
    def cog_unload(self):
        self.on = False
        for t in self.tasks:
            t.cancel()
            del t
        del self

        print("EVENT_COG: unloaded")

    ########################################## SCHEDULER ##########################################

    async def scheduler(self):
        guilds_configs = self.config.all_guilds()
        for guild_id, guild_config in guilds_configs.items():
            guild = self.bot.get_guild(guild_id)
            if guild:
                await self.add_events(
                    guild,
                    *(guild_config.get().events)
                )

    ######################################## EVENT COMMANDS #######################################

    @group()
    async def event(self, ctx: Context):
        pass

    @event.command()
    async def add(
        self, ctx: Context, channel: Union[int, str, TextChannel], time: str,
        title: str, *participants: Union[int, str, Member, Role]
    ):
        guild = ctx.guild

        try:
            # parsing title
            title = title[:200]

            # parsing date
            date = EventData.timestamp(time)

            # parsing participants (Member(s) or Role(s))
            async def convert(p: Union[int, str, Member, Role]):
                try:
                    return await RoleConverter().convert(ctx, str(p))
                except BadArgument:
                    try:
                        return await MemberConverter().convert(ctx, str(p))
                    except BadArgument:
                        raise InvalidArguments(
                            ctx=ctx,
                            title="Participant Error",
                            message="Couldn't find provided participants"
                        )
            participants = [await convert(p) for p in participants]

            # parsing channel
            try:
                channel = await TextChannelConverter().convert(ctx, str(channel))
                channel_id = channel.id
            except BadArgument:
                try: # keeping 0 value as a no-announcement-channel criterium
                    channel_id = int(channel)
                    if channel_id:
                        raise ValueError
                except ValueError:
                    raise InvalidArguments(
                        ctx=ctx,
                        title="Channel Error",
                        message="Couldn't find provided channel"
                    )

            guild_config = self.config.guild(guild)
            guild_data = guild_config.get()

            # checking if same event already exists
            events = ImprovedList(guild_data.events)
            try:
                events.index(
                    (title.lower(), date),
                    key=lambda e: (e.title.lower(), e.date)
                )
                raise InvalidArguments(
                    ctx=ctx,
                    title="Name Error",
                    message="There is another event on same date with same name"
                )
            except ValueError:
                pass

            # appending event
            event = EventData(
                channel=channel_id,
                date=date,
                participants=[p.id for p in participants],
                title=title
            )
            guild_data.events.append(event)
            guild_config.set(guild_data)

            # starting event scheduler
            await self.add_events(guild, event)

            embed = Embed(
                title="Event added",
                description=(
                    f"Title: {title}" + "\n"
                    f"Date: {event.datetime()}" + "\n"
                    f"Participants: {' '.join(map(lambda p: p.mention, participants))}"
                )
            )
            await ctx.send(embed=embed)

        except InvalidArguments as error:
            await error.execute()

    @event.command(name="list")
    async def list_(self, ctx: Context):
        guild = ctx.guild
        guild_config = self.config.guild(guild)
        guild_data= guild_config.get()

        events = [e for e in guild_data.events if not e.elapsed()]
        events = lexsorted(events, key=lambda e: (e.date, e.title))

        if events:
            def convert(p: int):
                ret = guild.get_member(p)
                if not ret:
                    ret = guild.get_role(p)
                return ret

            message = ""
            for event in events:
                participants = [c for p in event.participants if (c := convert(p))]
                message += (
                    f"{event.datetime()} - {event.title}: "
                    f"{', '.join(map(lambda p: p.mention, participants))}" + "\n"
                )
        else:
            message = "No future event"

        embed = Embed(
            title="Future Events List",
            description=message
        )
        await ctx.send(embed=embed)

    @event.command()
    async def remove(self, ctx: Context, title: str, time: str = None):
        guild_config = self.config.guild(ctx.guild)
        guild_data = guild_config.get()

        matches = [e for e in guild_data.events if e.title.lower() == title.lower()]
        try:
            if not matches:
                raise InvalidArguments(
                    ctx=ctx,
                    title="Title Error",
                    message="Couldn't find event with provided name"
                )
            elif len(matches) > 1:
                matches = [e for e in matches if str(e.date) == time]
                if not matches:
                    raise InvalidArguments(
                        ctx=ctx,
                        title="Date Error",
                        message="Couldn't find event with provided date"
                    )

        except InvalidArguments as error:
            await error.execute()

        else:
            match = matches[0]
            guild_data.events.remove(match)

            guild_config.set(guild_data)

            embed = Embed(
                title="Event Removed",
                description=match.datetime()
            )
            await ctx.send(embed=embed)

    ######################################## STATIC METHODS #######################################

    @staticmethod
    async def notify(guild: Guild, event: EventData):
        await sleep(event.how_far())

        channel = guild.get_channel(event.channel)

        if channel:
            def convert(p: int):
                ret = guild.get_member(p)
                if not ret:
                    ret = guild.get_role(p)
                return ret
            participants = [c for p in event.participants if (c := convert(p))]

            title = event.title

            message = " ".join(map(lambda p: p.mention, participants))
            embed = Embed(title=title)
            await channel.send(message, embed=embed)

    ########################################### METHODS ###########################################

    async def add_events(self, guild: Guild, *events: EventData):
        for event in events:
            if not event.elapsed():
                task = self.bot.loop.create_task(self.notify(guild, event))
                self.tasks.append(task)
