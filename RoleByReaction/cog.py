############################################# IMPORTS #############################################

#################### DISCORD ####################
from discord import (
    Embed,
    Emoji,
    Guild,
    Message,
    Member,
    RawReactionActionEvent,
    Reaction,
    Role
)
from discord import NotFound
from discord.ext.commands import (
    BadArgument,
    Bot,
    Cog,
    Context,
    EmojiConverter,
    RoleConverter
)
from discord.ext.commands import group

##################### DATA ######################
from .data import (
    Combination,
    Guild as GuildData
)
from .data import (
    EmojiType,
    RoleType
)

##################### UTILS #####################
from emoji import demojize
from typing import (
    Awaitable,
    Dict,
    List,
    Set,
    Union
)
from utils import (
    Config as Cfg,
    ImprovedList
)
from utils import revert_dict
from utils.checks import (
    admin,
    admin_or_permissions,
    ask_confirmation,
    can_give_role
)
from utils.exceptions import InvalidArguments

############################################### COGS ##############################################

class RoleByReaction(Cog):

    ######################################### CONSTRUCTOR #########################################

    def __init__(self, bot: Bot):
        self.bot = bot
        self.config = Cfg(self)

        self.defaults = GuildData(
            channel=0,
            combinations=list(),
            message=0,
            title="React with corresponding emoji to get role"
        )
        self.config.defaults_guild(self.defaults)

        self.bot.loop.create_task(self.startup_check())

    ########################################### UNLOADER ##########################################

    def cog_unload(self):
        del self

    ########################################## SCHEDULER ##########################################

    async def startup_check(self):
        await self.bot.wait_until_ready()

        guilds_configs = self.config.all_guilds()
        for guild_id, guild_config in guilds_configs.items():
            guild = self.bot.get_guild(guild_id)
            if guild:
                guild_data = guild_config.get()
                await self._treat_guild(guild, guild_data)

    ########################################### EVENTS ############################################

    async def _treat_payload(self, payload: RawReactionActionEvent):
        guild = self.bot.get_guild(payload.guild_id)
        if guild:
            guild_config = self.config.guild(guild)
            guild_data = guild_config.get()
            await self._treat_reaction(guild, guild_data, payload)

    @Cog.listener()
    async def on_raw_reaction_add(self, payload: RawReactionActionEvent):
        await self._treat_payload(payload)

    @Cog.listener()
    async def on_raw_reaction_remove(self, payload: RawReactionActionEvent):
        await self._treat_payload(payload)

    ################################## ROLE BY REACTION COMMANDS ##################################

    @admin_or_permissions()
    @group()
    async def rbr(self, ctx: Context):
        pass

    @admin()
    @rbr.command()
    async def title(self, ctx: Context, *, title: str):
        guild_config = self.config.guild(ctx.guild)
        guild_data = guild_config.get()

        guild_data.title = title
        await self._edit_rbr_message(ctx, guild_data)

        guild_config.set(guild_data)

        embed = Embed(
            title='Title Changed',
            description=f'Successfully updated title to {title}'
        )
        await ctx.send(embed=embed)

    @admin_or_permissions(manage_roles=True)
    @rbr.command()
    async def add(self, ctx: Context, emoji: EmojiType, *, role: RoleType):
        guild = ctx.guild
        guild_config = self.config.guild(guild)
        guild_data = guild_config.get()

        combinations = guild_data.combinations

        try:
            emoji = await self.import_emoji(ctx, emoji)
            if emoji in [c.emoji for c in combinations]:
                raise InvalidArguments(
                    ctx=ctx,
                    title="Role Error",
                    message=f"Role {role} already used"
                )

            role = await self.import_role(ctx, role)
            if role.id in [c.role for c in combinations]:
                raise InvalidArguments(
                    ctx=ctx,
                    title="Role Error",
                    message=f"Role {role} already used"
                )

            if not can_give_role(role, ctx.me):
                raise InvalidArguments(
                    ctx=ctx,
                    title="Role Error",
                    message=f"Bot doesn't have enough rights to give role"
                )
        except InvalidArguments as error:
            await error.execute()

        else:
            new = Combination(
                emoji=emoji.id if hasattr(emoji, "id") else emoji,
                role=role.id
            )
            combinations.append(new)

            guild_data.combinations = combinations
            await self._edit_rbr_message(ctx, guild_data)

            guild_config.set(guild_data)

            embed = Embed(
                title="Combination Added",
                description=f"{emoji} successfully linked with {role}"
            )
            await ctx.send(embed=embed)

    @admin_or_permissions(manage_roles=True)
    @rbr.command()
    async def remove(self, ctx: Context, *, element: Union[EmojiType, RoleType]):
        guild = ctx.guild
        guild_config = self.config.guild(guild)
        guild_data = guild_config.get()

        combinations = guild_data.combinations

        try:
            if not combinations:
                raise InvalidArguments(
                    ctx=ctx,
                    title="Data Error",
                    message="No data registered yet"
                )

            try:
                element = await self.import_emoji(ctx, element)
                element = element.id if hasattr(element, "id") else element
                var = "emoji"
            except InvalidArguments:
                try:
                    role = await self.import_role(ctx, element)
                    element = role.id
                    var = "role"
                except InvalidArguments:
                    raise InvalidArguments(
                        ctx=ctx,
                        message="Reference not found"
                    )

            if element not in [c[var] for c in combinations]:
                raise InvalidArguments(
                    ctx=ctx,
                    message="Argument wasn't found in data"
                )
        except InvalidArguments as error:
            await error.execute()

        else:
            for combination in combinations:
                if combination[var] == element:
                    combinations.remove(combination)
                    break

            guild_data.combinations = combinations
            await self._edit_rbr_message(ctx, guild_data)

            guild_config.set(guild_data)

            emoji = await self.import_emoji(ctx, combination.emoji)
            role = guild.get_role(combination.role)

            embed = Embed(
                title="Combination Removed",
                description=f"{emoji} and {role} successfully unlinked"
            )
            await ctx.send(embed=embed)

    @admin()
    @rbr.command()
    async def create(self, ctx: Context):
        guild = ctx.guild
        guild_config = self.config.guild(guild)
        guild_data = guild_config.get()

        embed = self._rbr_message_content(guild, guild_data)
        message = await ctx.send(embed=embed)
        await self._add_reactions(
            ctx=ctx,
            message=message,
            emojis=[c.emoji for c in guild_data.combinations]
        )

        guild_data.channel = message.channel.id
        guild_data.message = message.id
        guild_config.set(guild_data)

    @admin()
    @rbr.command()
    async def message(self, ctx: Context, channel_id: int, message_id: int):
        guild = ctx.guild
        guild_config = self.config.guild(guild)
        guild_data = guild_config.get()

        guild_data.channel = channel_id
        guild_data.message = message_id
        try:
            message = await self._edit_rbr_message(ctx, guild_data)
        except InvalidArguments as error:
            await error.execute()

        else:
            guild_config.set(guild_data)

            embed = Embed(
                title="Message Set",
                description=f"[jump to]({message.jump_url})"
            )
            await ctx.send(embed=embed)

    @admin_or_permissions(manage_roles=True)
    @rbr.command()
    async def show(self, ctx: Context):
        guild = ctx.guild
        guild_config = self.config.guild(guild)
        guild_data = guild_config.get()

        guild_data.title = "Role By Reaction Template"

        embed = self._rbr_message_content(guild, guild_data)
        await ctx.send(embed=embed)

    @admin()
    @rbr.command()
    async def reset(self, ctx: Context):
        answer = await ask_confirmation(ctx)
        if answer:
            guild = ctx.guild
            self.config.guild(guild).set(self.defaults)

            embed = Embed(
                title="Data Reset"
            )
            await ctx.send(embed=embed)

        else:
            embed = Embed(
                title="Cancelled"
            )
            await ctx.send(embed=embed)

    @admin()
    @rbr.command()
    async def update(self, ctx: Context):
        guild = ctx.guild
        guild_config = self.config.guild(guild)
        guild_data = guild_config.get()

        try:
            await self._edit_rbr_message(ctx, guild_data)
        except InvalidArguments as error:
            await error.execute()

    ######################################## CLASS METHODS ########################################

    @classmethod
    async def _add_reactions(cls, ctx: Context, message: Message, emojis: List[Union[int, str]]):
        for emoji in emojis:
            try:
                emoji = ImprovedList(ctx.guild.emojis).get_item(
                    emoji,
                    key=lambda e: e.id
                )
                await message.add_reaction(emoji)
            except ValueError:
                try:
                    await message.add_reaction(str(emoji))
                except:
                    print(f"ROLEBYREACTION_COG: couldn't react with {emoji} on {message.jump_url}")

    @classmethod
    async def _edit_rbr_message(cls, ctx: Context, guild_data: GuildData) -> Message:
        guild = ctx.guild
        channel_id = guild_data.channel
        message_id = guild_data.message
        combinations = guild_data.combinations

        message = await cls._find_rbr_message(guild, guild_data, ctx)
        if message.author.id == ctx.me.id:
            embed = cls._rbr_message_content(guild, guild_data)
            await message.edit(embed=embed)
            await cls._add_reactions(
                ctx=ctx,
                message=message,
                emojis=[c.emoji for c in combinations]
            )
            return message

        else:
            raise InvalidArguments(
                ctx=ctx,
                title="Message Error",
                description="Linked message isn't from bot"
            )

    @classmethod
    async def _treat_guild(cls, guild: Guild, guild_data: GuildData):
        try:
            message = await cls._find_rbr_message(guild, guild_data)
        except InvalidArguments: # message not found
            pass

        else:
            reactions_state = await cls._make_reactions_state(guild, guild_data, message.reactions)
            members_state = cls._make_members_state(guild, guild_data)

            to_add, to_remove = cls._compare_reaction_members(reactions_state, members_state)
            await cls._edit_members_roles(to_add, to_remove)

    @classmethod
    async def _treat_reaction(
        cls, guild: Guild, guild_data: GuildData, payload: RawReactionActionEvent
    ):
        message_id = guild_data.message
        if payload.message_id == message_id:
            combinations = guild_data.combinations

            emoji = payload.emoji
            emoji = emoji.id if emoji.id else str(emoji)

            role = None
            for c in combinations:
                if c.emoji == emoji:
                    role = guild.get_role(c.role)
                    break

            if role:
                member = guild.get_member(payload.user_id)
                if member:
                    method = cls._get_role_method(
                        member=member,
                        event_type=payload.event_type
                    )
                    await method(role)

    ####################################### STATIC METHODS ########################################

    @staticmethod
    def _compare_reaction_members(
        react_state: Dict[Member, Set[Role]], memb_state: Dict[Member, Set[Role]]
    ) -> Dict[Member, Set[Role]] and Dict[Member, Set[Role]]:
        # Dict[Member, Set[Role]]
        add = dict()
        for member in react_state.keys():
            member_add = react_state[member] - memb_state.get(member, set())
            if member_add:
                add[member] = member_add

        # Dict[Member, Set[Role]]
        remove = dict()
        for member in memb_state.keys():
            member_remove = memb_state[member] - react_state.get(member, set())
            if member_remove:
                remove[member] = member_remove

        return add, remove

    @staticmethod
    async def _edit_members_roles(add: Dict[Member, Set[Role]], remove: Dict[Member, Set[Role]]):
        for member, roles in add.items():
            await member.add_roles(*roles)

        for member, roles in remove.items():
            await member.remove_roles(*roles)

    @staticmethod
    async def _find_rbr_message(guild: Guild, guild_data: GuildData, ctx: Context=None) -> Message:
        channel_id = guild_data.channel
        message_id = guild_data.message

        channel = guild.get_channel(channel_id)
        if channel:
            try:
                return await channel.fetch_message(message_id)
            except NotFound:
                raise InvalidArguments(
                    ctx=ctx,
                    title="Message Not Found",
                    message="Message doesn't exist or not provided"
                )
        else:
            raise InvalidArguments(
                ctx=ctx,
                title="Channel Not Found",
                message="Channel doesn't exist or not provided"
            )

    @staticmethod
    def _get_role_method(member: Member, event_type: str) -> Awaitable:
        if event_type == "REACTION_ADD":
            async def method(role):
                await member.add_roles(role)

        elif event_type == "REACTION_REMOVE":
            async def method(role):
                await member.remove_roles(role)

        else:
            async def method(role):
                return

        return method

    @staticmethod
    def _make_members_state(guild: Guild, guild_data: GuildData) -> Dict[Member, Set[Role]]:
        members = guild.members
        roles = [c.role for c in guild_data.combinations]

        return {member: {role for role in member.roles if role.id in roles} for member in members}

    @staticmethod
    async def _make_reactions_state(
        guild: Guild, guild_data: GuildData, reactions: List[Reaction]
    ) -> Dict[Member, Set[Role]]:
        combinations = guild_data.combinations

        # Dict[Role, Set[Member]]
        state_by_role = dict()
        for reaction in reactions:
            emoji = reaction.emoji
            try:
                combination = ImprovedList(combinations).get_item(
                    v=emoji.id if hasattr(emoji, "id") else str(emoji),
                    key=lambda c: c.emoji
                )
            except ValueError: # emoji not registered in combinations list
                continue

            else:
                role = guild.get_role(combination.role)
                if role: # role might have been deleted, so excluding None case
                    # Set[Member]
                    members = set()
                    async for user in reaction.users():
                        # excluding non-Members and self-reaction cases
                        if isinstance(user, Member) and user != guild.me:
                            members.add(user)

                    state_by_role[role] = members

        return revert_dict(state_by_role)

    @staticmethod
    def _rbr_message_content(guild: Guild, guild_data: GuildData) -> Embed:
        title = guild_data.title
        combinations = guild_data.combinations

        if combinations:
            content = ""
            for combination in combinations:
                emoji = combination.emoji
                try:
                    emoji = ImprovedList(guild.emojis).get_item(
                        emoji,
                        key=lambda e: e.id
                    )
                except ValueError:
                    pass

                role = guild.get_role(combination.role)
                if not role: # Role does not exist case
                    continue

                content += f"{emoji} - {role.name}" + "\n"

        else:
            content = "No combination registered yet"

        return Embed(
            title=title,
            description=content
        )

    @staticmethod
    async def import_emoji(ctx: Context, emoji: EmojiType) -> Union[str, Emoji]:
        emoji = str(emoji)

        try:
            emoji = await EmojiConverter().convert(ctx, emoji)
        except BadArgument:
            temp = demojize(emoji)
            if any([emoji == temp,               # Not an emoji
                    temp.count(":") != 2,        # More or less than an emoji
                    not temp.startswith(":"),    # More than an emoji
                    not temp.endswith(":")]):    # More than an emoji
                raise InvalidArguments(
                    ctx=ctx,
                    title="Emoji Error",
                    message=f"Couldn't load {emoji} emoji"
                )

        return emoji

    @staticmethod
    async def import_role(ctx: Context, role: RoleType) -> Role:
        try:
            return await RoleConverter().convert(ctx, str(role))
        except BadArgument:
            raise InvalidArguments(
                ctx=ctx,
                title="Role Error",
                message=f"Couldn't load {role} role"
            )
