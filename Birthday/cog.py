############################################# IMPORTS #############################################
#################### DISCORD ####################
from discord import (
    Embed,
    Member,
    Guild,
    TextChannel,
    Role
)
from discord.ext.commands import (
    Bot,
    Cog,
    Context,
    RoleConverter,
    TextChannelConverter
)
from discord.ext.commands import group
from discord.ext.commands import BadArgument

##################### DATA ######################
from .data import (
    Date,
    Guild as GuildData,
    Member as MemberData
)

##################### UTILS #####################
from asyncio import sleep
from datetime import (
    datetime as dt,
    timedelta as td
)
from typing import (
    Dict,
    List,
    Union
)
from utils import (
    Config as Cfg,
    Group
)
from utils.checks import (
    admin,
    ask_confirmation,
    can_give_role
)
from utils.exceptions import InvalidArguments

import numpy as np
import time

############################################# GLOBALS #############################################

MONTHS = [
    "Jan", "Feb", "Mar", "Apr",
    "May", "Jun", "Jul", "Aug",
    "Sep", "Oct", "Nov", "Dec"
]

############################################### COGS ##############################################

class Birthday(Cog):

    ######################################### CONSTRUCTOR #########################################

    def __init__(self, bot: Bot):
        self.bot = bot

        self.config = Cfg(self)

        self.defaults_guild = GuildData(channel=0, role=0)
        self.config.defaults_guild(self.defaults_guild)

        self.defaults_member = MemberData(
            birthday=Date(day=None, month=None),
            name="Unknown"
        )
        self.config.defaults_member(self.defaults_member)

        self.on = True
        self.bot.loop.create_task(self.scheduler())
        print("BIRTHDAY_COG: Scheduler started.")

    ########################################### UNLOADER ##########################################

    def cog_unload(self):
        self.on = False
        del self

        print("BIRTHDAY_COG: Scheduler stopped.")

    ########################################## SCHEDULER ##########################################

    @staticmethod
    def update_names(members_configs: Dict[Member, Group]):
        for member, group in members_configs.items():
            member_data = group.get()
            member_data.name = member.name
            group.set(member_data)

    @staticmethod
    async def treat_members(channel: TextChannel, to_treat: List[Member]):
        for member in to_treat:
            await channel.send(f":tada: Happy birthday {member.mention}!!! :cake:")

    @staticmethod
    async def treat_role(role: Role, to_treat: List[Member]):
        for member in role.guild.members:
            roles = member.roles

            if (member in to_treat) and (role not in roles):
                await member.add_roles(role)

            elif (member not in to_treat) and (role in roles):
                await member.remove_roles(role)

    async def treat_guild(self, guild: Guild):
        guild_config = self.config.guild(guild)

        # importing guild
        guild_data = guild_config.get()

        # importing members
        # Dict[int, Group]
        members_configs = self.config.all_members(guild)
        # Dict[Member, Group]
        members_configs = {guild.get_member(i): g for i, g in members_configs.items()}
        # Dict[Member, Group]
        members_configs = {m: g for m, g in members_configs.items() if m}

        # keeping trace of member names in case of they leave the server
        self.update_names(members_configs)

        # matching current date with birthdays
        today = Date(day=dt.now().day, month=dt.now().month)
        # Dict[Member, Date]
        m_birthdays = {m: g.get().birthday for m, g in members_configs.items()}
        # List[Member]
        to_treat = [m for m, b in m_birthdays.items() if today == b]

        # sending birthday message
        channel_id = guild_data.channel
        channel = guild.get_channel(channel_id)
        if channel:
            await self.treat_members(channel, to_treat)

        # updating roles
        role_id = guild_data.role
        role = guild.get_role(role_id)
        if role and can_give_role(role, guild.me):
            await self.treat_role(role, to_treat)

    async def wait_for_tomorrow(self):
        now = dt.now()
        date = dt.fromordinal(dt.today().toordinal())
        next_day = date + td(days=1)
        wait_time = (next_day - now).total_seconds()
        await sleep(
            wait_time,
            loop=self.bot.loop
        )

    async def scheduler(self):
        while self.on:
            await self.wait_for_tomorrow()

            if self.on:
                print("New day!")
                guilds_configs = self.config.all_guilds()
                for guild_id, guild_config in guilds_configs.items():
                    guild = self.bot.get_guild(guild_id)
                    if guild:
                        await self.treat_guild(guild)

    ###################################### BIRTHDAY COMMANDS ######################################

    @group()
    async def birthday(self, ctx: Context):
        pass

    @admin()
    @birthday.command()
    async def check(self, ctx: Context):
        await self.treat_guild(ctx.guild)

    @admin()
    @birthday.command()
    async def channel(self, ctx: Context, *, channel: Union[int, str, TextChannel]):
        """**[#channel or channel name]** :
        sets the channel where to send notifiations.
        """
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
    @birthday.command()
    async def role(self, ctx: Context, *, role: Union[int, str, Role]):
        """**[@role or role name]** :
        sets the role to give during birthday.
        """
        try:
            if not isinstance(role, Role):
                role = await RoleConverter().convert(ctx, str(role))
        except BadArgument:
            error = InvalidArguments(
                ctx=ctx,
                title='Role Error',
                message='Role not found or not provided'
            )
            await error.execute()
            return

        else:
            guild_config = self.config.guild(ctx.guild)
            guild_data = guild_config.get()
            guild_data.channel = role.id
            guild_config.set(guild_data)

            embed = Embed(
                title='Role Changed',
                description=f'Successfully updated role to {role.mention}'
            )
            await ctx.send(embed=embed)

    @birthday.command(name='set')
    async def set_(self, ctx: Context, day: int, month: int):
        """**[day] [month]** : Sets birthday date. Will send a server notification
         on the precised day.
        """
        day = f"0{day}" if day < 10 else str(day)
        month = f"0{month}" if month < 10 else str(month)

        try:
            date = time.strptime(f"{day} {month}", "%d %m")
        except ValueError:
            error = InvalidArguments(
                ctx=ctx,
                title="Date Error",
                message="Couldn't understand provided date"
            )
            await error.execute()
            return

        else:
            member = ctx.author
            member_config = self.config.member(member)

            member_data = MemberData(
                birthday=Date(
                    day=date.tm_mday,
                    month=date.tm_mon
                ),
                name=member.name
            )

            member_config.set(member_data)

            embed = Embed(
                title="Birthday Set!",
                description=f"Birthday set to {date.tm_mday} {MONTHS[date.tm_mon - 1]}"
            )
            await ctx.send(embed=embed)

    @birthday.command()
    async def remove(self, ctx: Context):
        """ : Removes date from birthdays list."""
        member = ctx.author
        member_config = self.config.member(member)

        new = self.defaults_member.copy()
        new.name = member.name

        member_config.set(new)

        embed = Embed(
            title="Birthday Reset",
            description="Birthday has been removed from database"
        )
        await ctx.send(embed=embed)

    @birthday.command(name='list')
    async def list_(self, ctx: Context):
        """ : Shows birthdays list."""
        guild = ctx.guild
        members_configs = self.config.all_members(guild)

        # Dict[int, _Member]
        members_data = {i: g.get() for i, g in members_configs.items()}

        # Dict[str, Date]
        members_birthdays = dict()
        for member_id, member_data in members_data.items():
            member = guild.get_member(member_id)

            member_name = member.name if member else member_data.name

            birthday = member_data.birthday
            if birthday != self.defaults_member.birthday:
                members_birthdays[member_name] = member_data.birthday

        if members_birthdays:
            # preparing data for sorting

            # List[Member], List[Date]
            members, birthdays = [l for l in zip(*(members_birthdays.items()))]
            # List[int], List[int]
            days, months = [l for l in zip(*[(b.day, b.month) for b in birthdays])]
            # List[int]
            order = np.lexsort((members, days, months))
            # List[Tuple[Member and Date]]
            sorted_birthdays = [(members[i], birthdays[i]) for i in order]

            message = ""
            for member, birthday in sorted_birthdays:
                message += f"{member} - {birthday.day}/{birthday.month}" + "\n"

            embed = Embed(
                title="Birthdays List",
                description=message
            )
            await ctx.send(embed=embed)

        else:
            embed = Embed(
                title="Birthdays List",
                description="No birthday recorded yet"
            )
            await ctx.send(embed=embed)
