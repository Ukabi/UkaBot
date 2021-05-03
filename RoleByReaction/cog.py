############################################# IMPORTS #############################################

#################### DISCORD ####################
from discord import (
    Embed,
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
from utils import can_give_role
from utils.checks import (
    admin,
    admin_or_permissions,
    ask_confirmation
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

    async def find_rbr_message(
        self, guild: Guild, channel_id: int, message_id: int, ctx: Context = None
    ) -> Message:
        channel = guild.get_channel(channel_id)
        if channel:
            try:
                message = await channel.fetch_message(message_id)
                return message
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

    async def make_reactions_state(
        self, reactions: List[Reaction], guild: Guild, combinations: List[Combination]
    ) -> Dict[int, Set[int]]:
        # Dict[int, Set[int]]
        state_by_role = dict()
        for reaction in reactions:
            try:
                combination = ImprovedList(combinations).get_item(
                    v=str(reaction.emoji),
                    key=lambda c: c.emoji
                )
            except ValueError: # emoji not registered in combinations list
                continue

            else:
                role = combination.role

                # Set[int]
                members = set()
                async for user in reaction.users():
                    if user.id != self.bot.user.id and isinstance(user, Member):
                        members.add(user.id)

                state_by_role[role] = members

        # Set[int]
        members = set().union(*(state_by_role.values()))

        # Dict[int, Set[int]]
        state_by_members = dict()
        for member in members:
            roles = {r for r, ms in state_by_role.items() if member in ms}
            state_by_members[member] = roles

        return state_by_members

    def make_members_state(self, guild: Guild, roles: List[int]) -> Dict[int, Set[int]]:
        # Dict[int, Set[int]]
        state = dict()
        for member in guild.members:
            state[member.id] = {role.id for role in member.roles if role.id in roles}

        return state

    def compare_reaction_members(
        self, react_state: Dict[int, Set[int]], memb_state: Dict[int, Set[int]]
    ) -> Dict[int, List[int]] and Dict[int, List[int]]:
        # Dict[int, Set[int]]
        add_roles = dict()
        for member in react_state.keys():
            to_add = react_state[member] - memb_state.get(member, set())
            add_roles[member] = list(to_add)

        # Dict[int, Set[int]]
        remove_roles = dict()
        for member in memb_state.keys():
            to_remove = memb_state[member] - react_state.get(member, set())
            remove_roles[member] = list(to_remove)
        # removing empty fields
        remove_roles = {member: roles for member, roles in remove_roles.items() if roles}

        return add_roles, remove_roles

    async def edit_members_roles(
        self, guild: Guild,
        to_add: Dict[int, List[int]], to_remove: Dict[int, List[int]]
    ):
        for member, roles in to_add.items():
            member = guild.get_member(member)
            if member:
                roles = [guild.get_role(role) for role in roles]
                await member.add_roles(*[role for role in roles if role])

        for member, roles in to_remove.items():
            member = guild.get_member(member)
            if member:
                roles = [guild.get_role(role) for role in roles]
                await member.remove_roles(*[role for role in roles if role])

    async def treat_guild(self, guild: Guild, guild_data: GuildData):
        channel_id = guild_data.channel
        message_id = guild_data.message
        combinations = guild_data.combinations

        try:
            message = await self.find_rbr_message(
                guild=guild,
                channel_id=channel_id,
                message_id=message_id
            )
        except InvalidArguments: # message not found
            pass

        else:
            reactions_state = await self.make_reactions_state(
                guild=guild,
                reactions=message.reactions,
                combinations=combinations
            )
            members_state = self.make_members_state(
                guild=guild,
                roles=[c.role for c in combinations]
            )

            to_add, to_remove = self.compare_reaction_members(
                react_state=reactions_state,
                memb_state=members_state
            )
            await self.edit_members_roles(
                guild=guild,
                to_add=to_add,
                to_remove=to_remove
            )

    async def startup_check(self):
        await self.bot.wait_until_ready()

        guilds_configs = self.config.all_guilds()
        for guild_id, guild_config in guilds_configs.items():
            guild = self.bot.get_guild(guild_id)
            if guild:
                guild_data = guild_config.get()
                await self.treat_guild(guild, guild_data)

    ########################################### EVENTS ############################################

    async def _get_role_method(self, member: Member, event_type: str) -> Awaitable:
        if event_type == "REACTION_ADD":
            async def method(role):
                await member.add_roles(role)

        elif event_type == "REACTION_REMOVE":
            async def method(role):
                await member.remove_roles(role)

        else:
            async def method(role):
                pass

        return method

    async def _treat_payload(self, payload: RawReactionActionEvent):
        guild = self.bot.get_guild(payload.guild_id)
        guild_config = self.config.guild(guild)
        guild_data = guild_config.get()

        message_id = guild_data.message
        if payload.message_id == message_id:
            combinations = guild_data.combinations
            emoji = str(payload.emoji)

            role = None
            for c in combinations:
                if c.emoji == emoji:
                    role = guild.get_role(c.role)
                    break

            if role:
                member = guild.get_member(payload.user_id)
                if member:
                    method = await self._get_role_method(
                        member=member,
                        event_type=payload.event_type
                    )
                    await method(role)

    @Cog.listener()
    async def on_raw_reaction_add(self, payload: RawReactionActionEvent):
        await self._treat_payload(payload)

    @Cog.listener()
    async def on_raw_reaction_remove(self, payload: RawReactionActionEvent):
        await self._treat_payload(payload)

    ################################## ROLE BY REACTION COMMANDS ##################################

    async def import_emoji(self, ctx: Context, emoji: EmojiType) -> str:
        emoji = str(emoji)

        try:
            emoji = str(await EmojiConverter().convert(ctx, emoji))
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

    async def import_role(self, ctx: Context, role: RoleType) -> Role:
        try:
            return await RoleConverter().convert(ctx, str(role))
        except BadArgument:
            raise InvalidArguments(
                ctx=ctx,
                title="Role Error",
                message=f"Couldn't load {role} role"
            )

    async def add_reactions(self, ctx: Context, message: Message, emojis: List[str]):
        for emoji in emojis:
            try:
                emoji = await self.import_emoji(ctx, emoji)
                await message.add_reaction(emoji)
            except InvalidArguments or NotFound:
                print(f"ROLEBYREACTION_COG: couldn't react with {emoji} on {message.jump_url}")

    def rbr_message_content(
        self, guild: Guild, title: str, combinations: List[Combination]
    ) -> Embed:
        guild_data = self.config.guild(guild).get()

        content = "" if combinations else "No combination registered yet"
        for combination in combinations:
            emoji = combination.emoji
            role = guild.get_role(combination.role)

            content += f"{emoji} - {role.name}" + "\n"

        return Embed(
            title=title,
            description=content
        )

    async def edit_rbr_message(
        self, ctx: Context, channel_id: int, message_id: int, title: str,
        combinations: List[Combination]
    ) -> Message:
        guild = ctx.guild

        message = await self.find_rbr_message(guild, channel_id, message_id, ctx)
        if message.author.id == ctx.me.id:
            embed = self.rbr_message_content(guild, title, combinations)
            await message.edit(embed=embed)
            await self.add_reactions(
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

            new = Combination(
                emoji=emoji,
                role=role.id
            )
            combinations.append(new)

            await self.edit_rbr_message(
                ctx=ctx,
                channel_id=guild_data.channel,
                message_id=guild_data.message,
                title=guild_data.title,
                combinations=combinations
            )

            guild_data[self.COMBINATIONS] = combinations
            guild_config.set(guild_data)

            embed = Embed(
                title="Combination Added",
                description=f"{emoji} successfully linked with {role}"
            )
            await ctx.send(embed=embed)

        except InvalidArguments as error:
            await error.execute()

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
                var = self.EMOJI
            except InvalidArguments:
                try:
                    role = await self.import_role(ctx, element)
                    element = role.id
                    var = self.ROLE
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

            for combination in combinations:
                if combination[var] == element:
                    combinations.remove(combination)
                    break

            await self.edit_rbr_message(
                ctx=ctx,
                channel_id=guild_data.channel,
                message_id=guild_data.message,
                title=guild_data.title,
                combinations=combinations
            )

            guild_data.combinations = combinations
            guild_config.set(guild_data)

            emoji = await EmojiConverter().convert(ctx, combination.emoji)
            role = guild.get_role(combination.role)

            embed = Embed(
                title="Combination Removed",
                description=f"{emoji} and {role} successfully unlinked"
            )
            await ctx.send(embed=embed)

        except InvalidArguments as error:
            await error.execute()

    @admin()
    @rbr.command()
    async def create(self, ctx: Context):
        guild = ctx.guild
        guild_config = self.config.guild(guild)
        guild_data = guild_config.get()

        embed = self.rbr_message_content(
            guild=guild,
            title=guild_data.title,
            combinations=guild_data.combinations
        )
        message = await ctx.send(embed=embed)
        await self.add_reactions(
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

        try:
            message = await self.edit_rbr_message(
                ctx=ctx,
                channel_id=channel_id,
                message_id=message_id,
                title=guild_data.title,
                combinations=guild_data.combinations
            )

            guild_data[self.CHANNEL] = channel_id
            guild_data[self.MESSAGE] = message_id
            guild_config.set(guild_data)

            embed = Embed(
                title="Message Set",
                description=f"[jump to]({message.jump_url})"
            )
            await ctx.send(embed=embed)

        except InvalidArguments as error:
            await error.execute()

    @admin_or_permissions(manage_roles=True)
    @rbr.command()
    async def show(self, ctx: Context):
        guild = ctx.guild
        guild_config = self.config.guild(guild)
        guild_data = guild_config.get()

        embed = self.rbr_message_content(
            guild=guild,
            title="Role By Reaction Template",
            combinations=guild_data.combinations
        )
        await ctx.send(embed=embed)

    @admin()
    @rbr.command()
    async def reset(self, ctx: Context):
        answer = await ask_confirmation(
            ctx=ctx,
            bot=self.bot
        )
        if answer:
            guild = ctx.guild

            self.config.guild(guild).set(self.defaults_guild)

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
            await self.edit_rbr_message(
                ctx=ctx,
                channel_id=guild_data.channel,
                message_id=guild_data.message,
                title=guild_data.title,
                combinations=guild_data.combinations
            )

        except InvalidArguments as error:
            await error.execute()
