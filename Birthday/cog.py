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
from asyncio import AbstractEventLoop
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
    can_give_role
)
from utils.exceptions import InvalidArguments

import numpy as np

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

    async def scheduler(self):
        while self.on:
            await self.wait_for_tomorrow(self.bot.loop)
            if self.on:
                print("New day!")
                guilds_configs = self.config.all_guilds()
                for guild_id, guild_config in guilds_configs.items():
                    guild = self.bot.get_guild(guild_id)
                    if guild:
                        await self.treat_guild(
                            guild,
                            guild_config.get(),
                            self.config.all_members(guild)
                        )

    ###################################### BIRTHDAY COMMANDS ######################################

    @group()
    async def birthday(self, ctx: Context):
        pass

    @admin()
    @birthday.command()
    async def check(self, ctx: Context):
        guild = ctx.guild
        await self.treat_guild(
            guild,
            self.config.guild(guild).get(),
            self.config.all_members(guild)
        )

    @admin()
    @birthday.command()
    async def channel(self, ctx: Context, *, channel: Union[int, str, TextChannel]):
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
        try:
            date = Date.convert_date(day=day, month=month)
        except ValueError:
            error = InvalidArguments(
                ctx=ctx,
                title="Date Error",
                message="Couldn't understand provided date"
            )
            await error.execute()

        else:
            member = ctx.author
            member_config = self.config.member(member)

            member_data = MemberData(
                birthday=date,
                name=member.name
            )

            member_config.set(member_data)

            embed = Embed(
                title="Birthday Set",
                description=f"Birthday set to {date}"
            )
            await ctx.send(embed=embed)

    @birthday.command()
    async def remove(self, ctx: Context):
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
        guild = ctx.guild
        members_configs = self.config.all_members(guild)

        # Dict[int, _Member]
        members_data = {i: g.get() for i, g in members_configs.items()}

        # List[Tuple[str and int and int]]
        to_sort = []
        for member_id, member_data in members_data.items():
            if not member_data.birthday: # None case
                continue

            member = guild.get_member(member_id)
            if member: # Member not found case
                member_data.name = member.name
            
            to_sort.append(member_data.sorting_format())

        if to_sort:
            # List[int]
            order = np.lexsort(tuple(zip(*to_sort)))
            # List[MemberData]
            sorted_birthdays = MemberData.from_order(to_sort, order)

            message = "\n".join(str(member) for member in sorted_birthdays)
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

    ######################################## CLASS METHODS ########################################

    @classmethod
    async def treat_guild(cls, guild: Guild, guild_data: GuildData, members_configs: Dict[int, Group]):
        # importing Members from their ids
        # Dict[Member, Group]
        members_configs = {guild.get_member(i): g for i, g in members_configs.items()}
        # Dict[Member, Group] with None cases filtered out
        members_configs = {m: g for m, g in members_configs.items() if m}

        # keeping trace of member names if they leave the server
        cls.update_names(members_configs)

        # matching current date with birthdays
        now = dt.now()
        today = Date(day=now.day, month=now.month)
        # Dict[Member, Date]
        members_birthdays = {m: g.get().birthday for m, g in members_configs.items()}
        # List[Member]
        to_treat = [m for m, b in members_birthdays.items() if today == b]

        # sending birthday message
        channel_id = guild_data.channel
        channel = guild.get_channel(channel_id)
        if channel:
            await cls.treat_members(channel, to_treat)

        # updating roles
        role_id = guild_data.role
        role = guild.get_role(role_id)
        if role and can_give_role(role, guild.me):
            await cls.treat_role(role, to_treat)

    ######################################## STATIC METHODS #######################################

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

    @staticmethod
    def update_names(members_configs: Dict[Member, Group]):
        for member, group in members_configs.items():
            member_data = group.get()
            member_data.name = member.name
            group.set(member_data)

    @staticmethod
    async def wait_for_tomorrow(loop: AbstractEventLoop):
        now = dt.now()
        date = dt.fromordinal(dt.today().toordinal())
        next_day = date + td(days=1)
        wait_time = (next_day - now).total_seconds()
        await sleep(
            wait_time,
            loop=loop
        )
