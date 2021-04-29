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
from discord.ext.commands import BadArgument

import discord.ext.commands as cmd

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
from utils import (
    objectify,
    update_config
)
from utils.checks import (
    admin,
    admin_or_permissions,
    ask_confirmation,
    can_give_role
)
from utils.exceptions import InvalidArguments

import numpy as np
import time

############################################### COGS ##############################################

class Birthday(Cog):
    MONTHS = [
        "Jan", "Feb", "Mar", "Apr",
        "May", "Jun", "Jul", "Aug",
        "Sep", "Oct", "Nov", "Dec"
    ]

    # For Guild config
    CHANNEL = "channel"
    ROLE = "role"

    # For Member config
    BIRTHDAY = "birthday"
    NAME = "name"

    # For Member.Birthday config
    DAY = "day"
    MONTH = "month"

    ######################################### CONSTRUCTOR #########################################

    def __init__(self, bot: Bot):
        super().__init__()
        self.bot = bot

        self.config = Cfg(self)

        self.defaults_guild = {
            self.CHANNEL: 0,
            self.ROLE: 0
        }
        self.config.defaults_guild(self.defaults_guild)

        self.defaults_member = {
            self.BIRTHDAY: {
                self.DAY: None,
                self.MONTH: None
            },
            self.NAME: "Unknown"
        }
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
    async def treat_members(channel: TextChannel, members: List[Member]):
        for member in members:
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
        guild_data = guild_config.get()

        members_configs = self.config.get_all_members(guild)
        members_configs = {guild.get_member(i): g for i, g in members_configs.items()}
        members_configs = {m: g for m, g in members_configs.items() if m}

        self.update_names(members_configs)

        m_birthdays = {m: g.get().birthday for m, g in members_configs.items()}

        date = {
            self.DAY: dt.now().day,
            self.MONTH: dt.now().month
        }
        to_treat = [m for m, b in m_birthdays.items() if date == b]

        channel_id = guild_data.channel
        channel = guild.get_channel(channel_id)
        if channel:
            await self.treat_members(channel, to_treat)

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
                guilds_configs = self.config.get_all_guilds()
                for guild_id, guild_config in guilds_configs.items():
                    guild = self.bot.get_guild(guild_id)
                    if guild:
                        await self.treat_guild(guild)

    ###################################### BIRTHDAY COMMANDS ######################################

    @cmd.group(name='birthday')
    async def birthday_group(self, ctx: Context):
        pass

    @admin()
    @birthday_group.command(name="check")
    async def birthday_check(self, ctx: Context):
        await self.treat_guild(ctx.guild)

    @admin()
    @birthday_group.command(name='channel')
    async def birthday_channel(self, ctx: Context, *, channel: Union[int, str, TextChannel]):
        """**[#channel or channel name]** :
        sets the channel where to send notifiations.
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
    @birthday_group.command(name='role')
    async def birthday_role(self, ctx: Context, *, role: Union[int, str, Role]):
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
            update_config(
                config=self.config.guild(ctx.guild),
                attribute=self.ROLE,
                value=role.id
            )

            embed = Embed(
                title='Role Changed',
                description=f'Successfully updated role to {role.mention}'
            )
            await ctx.send(embed=embed)

    @birthday_group.command(name='set')
    async def birthday_set(self, ctx: Context, day: int, month: int):
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

            member_data = {
                self.NAME: member.name,
                self.BIRTHDAY: {
                    self.DAY: date.tm_mday,
                    self.MONTH: date.tm_mon
                }
            }

            member_config.set(member_data)

            embed = Embed(
                title="Birthday Set!",
                description=f"Birthday set to {date.tm_mday} {self.MONTHS[date.tm_mon - 1]}"
            )
            await ctx.send(embed=embed)

    @birthday_group.command(name='remove')
    async def birthday_remove(self, ctx: Context):
        """ : Removes date from birthdays list."""
        member = ctx.author
        member_config = self.config.member(member)

        new = objectify(self.defaults_member.copy())
        new[self.NAME] = member.name

        member_config.set(new)

        embed = Embed(
            title="Birthday Reset",
            description="Birthday has been removed from database"
        )
        await ctx.send(embed=embed)

    @birthday_group.command(name='list')
    async def birthday_list(self, ctx: Context):
        """ : Shows birthdays list."""
        guild = ctx.guild
        members_configs = self.config.get_all_members(guild)

        members_data = {i: g.get() for i, g in members_configs.items()}

        members_birthdays = dict()
        for member_id, member_data in members_data.items():
            member = guild.get_member(member_id)

            member_name = member.name if member else member_data.name

            birthday = member_data.birthday
            if birthday != {self.DAY: None, self.MONTH: None}:
                members_birthdays[member_name] = member_data.birthday

        if members_birthdays:
            members, birthdays = [l for l in zip(*(members_birthdays.items()))]
            days, months = [l for l in zip(*[(b.day, b.month) for b in birthdays])]
            order = np.lexsort((members, days, months))
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
