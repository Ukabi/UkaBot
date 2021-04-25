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

##################### UTILS #####################
from datetime import datetime as dt
from emoji import demojize
from typing import (
    Awaitable,
    Dict,
    List,
    Set,
    Union
)
from utils import Config as Cfg
from utils import ImprovedList
from utils import (
    ask_confirmation,
    can_give_role,
    update_config
)
from utils.checks import (
    admin,
    admin_or_permissions
)
from utils.exceptions import InvalidArguments

############################################### COGS ##############################################

class RoleByReaction(Cog):
    TITLE = "title"
    CHANNEL = "channel"
    MESSAGE = "message"
    COMBINATIONS = "combinations"

    EMOJI = "emoji"
    ROLE = "role"

    ######################################### CONSTRUCTOR #########################################

    def __init__(self, bot: Bot):
        self.bot = bot
        self.config = Cfg(self)

        self.defaults_guild = {
            self.TITLE: "React with corresponding emoji to get role",
            self.CHANNEL: 0,
            self.MESSAGE: 0,
            self.COMBINATIONS: list()
        }
        self.config.defaults_guild(self.defaults_guild)

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
        self, reactions: List[Reaction], guild: Guild,
        combinations: List[Dict[str, Union[int, str]]]
    ) -> Dict[int, Set[int]]:
        state_by_role = dict()
        for reaction in reactions:
            try:
                combination = ImprovedList(combinations).get_item(
                    v=str(reaction.emoji),
                    key=lambda c: c[self.EMOJI]
                )
                role = combination[self.ROLE]

                members = set()
                async for user in reaction.users():
                    if user.id != self.bot.user.id and isinstance(user, Member):
                        members.add(user.id)

                state_by_role[role] = members

            except ValueError:
                continue

        members = set().union(*(state_by_role.values()))
        state_by_members = dict()
        for member in members:
            roles = {r for r, ms in state_by_role.items() if member in ms}
            state_by_members[member] = roles

        return state_by_members

    def make_members_state(
        self, guild: Guild, roles: List[int]
    ) -> Dict[int, Set[int]]:
        state = dict()
        for member in guild.members:
            state[member.id] = {role.id for role in member.roles if role.id in roles}

        return state

        # Just for the fun
        # return {member.id: {role.id for role in member.roles if role in roles} for member in guild.members}

    def compare_reaction_members(
        self, react_state: Dict[int, Set[int]], memb_state: Dict[int, Set[int]]
    ) -> Dict[int, List[int]] and Dict[int, List[int]]:
        add_roles = dict()
        for member in react_state.keys():
            to_add = react_state[member] - memb_state.get(member, set())
            add_roles[member] = list(to_add)

        remove_roles = dict()
        for member in memb_state.keys():
            to_remove = memb_state[member] - react_state.get(member, set())
            remove_roles[member] = list(to_remove)

        return add_roles, {member: roles for member, roles in remove_roles.items() if roles}

        # Just for the fun
        # return {member: role - memb_state.get(member, set()) for member, role in react_state.items()}, {member: role - react_state.get(member, set()) for member, role in memb_state.items()}

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

    async def treat_guild(self, guild: Guild):
        guild_config = self.config.guild(guild)
        guild_data = guild_config.get()

        channel_id = guild_data[self.CHANNEL]
        message_id = guild_data[self.MESSAGE]
        combinations = guild_data[self.COMBINATIONS]
        try:
            message = await self.find_rbr_message(
                guild=guild,
                channel_id=channel_id,
                message_id=message_id
            )

            reactions_state = await self.make_reactions_state(
                guild=guild,
                reactions=message.reactions,
                combinations=combinations
            )
            members_state = self.make_members_state(
                guild=guild,
                roles=[c[self.ROLE] for c in combinations]
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

        except InvalidArguments:
            pass

    async def startup_check(self):
        await self.bot.wait_until_ready()

        guilds_configs = self.config.get_all_guilds()
        for guild_id, guild_config in guilds_configs.items():
            guild = self.bot.get_guild(guild_id)
            if guild:
                await self.treat_guild(guild)

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

        message_id = guild_data[self.MESSAGE]
        if payload.message_id == message_id:
            combinations = guild_data[self.COMBINATIONS]
            emoji = str(payload.emoji)

            role = None
            for c in combinations:
                if c[self.EMOJI] == emoji:
                    role = guild.get_role(c[self.ROLE])
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

    async def import_emoji(
        self, ctx: Context, emoji: Union[int, str, Emoji]
    ) -> str:
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

    async def import_role(
        self, ctx: Context, role: Union[int, str, Role]
    ) -> Role:
        try:
            role = await RoleConverter().convert(ctx, str(role))
            return role
        except BadArgument:
            raise InvalidArguments(
                ctx=ctx,
                title="Role Error",
                message=f"Couldn't load {role} role"
            )

    async def add_reactions(
        self, ctx: Context, message: Message, emojis: List[str]
    ):
        for emoji in emojis:
            try:
                emoji = await self.import_emoji(ctx, emoji)
                await message.add_reaction(emoji)
            except InvalidArguments or NotFound:
                print(f"ROLEBYREACTION_COG: couldn't react with {emoji} on {message.jump_url}")

    def rbr_message_content(
        self, guild: Guild, title: str,
        combinations: List[Dict[str, Union[str, int]]]
    ) -> Embed:
        guild_data = self.config.guild(guild).get()

        content = "" if combinations else "No combination registered yet"
        for combination in combinations:
            emoji = combination.get(self.EMOJI)
            role = guild.get_role(combination.get(self.ROLE))

            content += f"{emoji} - {role.name}" + "\n"

        return Embed(
            title=title,
            description=content
        )

    async def edit_rbr_message(
        self, ctx: Context, channel_id: int, message_id: int, title: str,
        combinations: List[Dict[str, Union[int, str]]]
    ) -> Message:
        guild = ctx.guild

        message = await self.find_rbr_message(guild, channel_id, message_id, ctx)
        if message.author.id == ctx.me.id:
            embed = self.rbr_message_content(guild, title, combinations)
            await message.edit(embed=embed)
            await self.add_reactions(
                ctx=ctx,
                message=message,
                emojis=[c[self.EMOJI] for c in combinations]
            )
            return message

        else:
            raise InvalidArguments(
                ctx=ctx,
                title="Message Error",
                description="Linked message isn't from bot"
            )

    @admin_or_permissions()
    @group(name='rbr')
    async def rbr_group(self, ctx: Context):
        pass

    @admin()
    @rbr_group.command(name='title')
    async def rbr_title(self, ctx: Context, *, title: str):
        """**[text]** : edits the rbr message's title."""
        update_config(
            config=self.config.guild(ctx.guild),
            attribute=self.TITLE,
            value=title
        )

        embed = Embed(
            title='Message Changed',
            description=f'Successfully updated welcome message to {title}'
        )
        await ctx.send(embed=embed)

    @admin_or_permissions(manage_roles=True)
    @rbr_group.command(name='add')
    async def rbr_add(
        self, ctx: Context,
        emoji: Union[int, str, Emoji], *, role: Union[int, str, Role]
    ):
        """**[emoji] [role]** : links an emoji with a role."""
        guild = ctx.guild
        guild_config = self.config.guild(guild)
        guild_data = guild_config.get()

        combinations = guild_data[self.COMBINATIONS]

        try:
            emoji = await self.import_emoji(ctx, emoji)
            if emoji in [c[self.EMOJI] for c in combinations]:
                raise InvalidArguments(
                    ctx=ctx,
                    title="Role Error",
                    message=f"Role {role} already used"
                )

            role = await self.import_role(ctx, role)
            if role.id in [c[self.ROLE] for c in combinations]:
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

            new = {
                self.EMOJI: emoji,
                self.ROLE: role.id
            }
            combinations.append(new)

            await self.edit_rbr_message(
                ctx=ctx,
                channel_id=guild_data[self.CHANNEL],
                message_id=guild_data[self.MESSAGE],
                title=guild_data[self.TITLE],
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
    @rbr_group.command(name='remove')
    async def rbr_remove(
        self, ctx: Context, *, element: Union[int, str, Role, Emoji]
    ):
        """**[emoji or role]** : removes a link from the list."""
        guild = ctx.guild
        guild_config = self.config.guild(guild)
        guild_data = guild_config.get()

        combinations = guild_data[self.COMBINATIONS]

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
                channel_id=guild_data[self.CHANNEL],
                message_id=guild_data[self.MESSAGE],
                title=guild_data[self.TITLE],
                combinations=combinations
            )

            guild_data[self.COMBINATIONS] = combinations
            guild_config.set(guild_data)

            emoji = await EmojiConverter().convert(ctx, combination[self.EMOJI])
            role = guild.get_role(combination[self.ROLE])

            embed = Embed(
                title="Combination Removed",
                description=f"{emoji} and {role} successfully unlinked"
            )
            await ctx.send(embed=embed)

        except InvalidArguments as error:
            await error.execute()

    @admin()
    @rbr_group.command(name='create')
    async def rbr_create(self, ctx: Context):
        guild = ctx.guild
        guild_config = self.config.guild(guild)
        guild_data = guild_config.get()

        embed = self.rbr_message_content(
            guild=guild,
            title=guild_data[self.TITLE],
            combinations=guild_data[self.COMBINATIONS]
        )
        message = await ctx.send(embed=embed)
        await self.add_reactions(
            ctx=ctx,
            message=message,
            emojis=[c[self.EMOJI] for c in guild_data[self.COMBINATIONS]]
        )

        guild_data[self.CHANNEL] = message.channel.id
        guild_data[self.MESSAGE] = message.id
        guild_config.set(guild_data)

    @admin()
    @rbr_group.command(name='message')
    async def rbr_message(self, ctx: Context, channel_id: int, message_id: int):
        """: sends the role by reaction message members can react on."""
        guild = ctx.guild
        guild_config = self.config.guild(guild)
        guild_data = guild_config.get()

        try:
            message = await self.edit_rbr_message(
                ctx=ctx,
                channel_id=channel_id,
                message_id=message_id,
                title=guild_data[self.TITLE],
                combinations=guild_data[self.COMBINATIONS]
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
    @rbr_group.command(name='show')
    async def rbr_show(self, ctx: Context):
        """: shows the associations between emojis and role."""
        guild = ctx.guild
        guild_config = self.config.guild(guild)
        guild_data = guild_config.get()

        embed = self.rbr_message_content(
            guild=guild,
            title="Role By Reaction Template",
            combinations=guild_data[self.COMBINATIONS]
        )
        await ctx.send(embed=embed)

    @admin()
    @rbr_group.command(name='reset')
    async def rbr_reset(self, ctx: Context):
        """: resets the associations list."""
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
    @rbr_group.command(name='update')
    async def update_rbr_message(self, ctx: Context):
        guild = ctx.guild
        guild_config = self.config.guild(guild)
        guild_data = guild_config.get()

        try:
            await self.edit_rbr_message(
                ctx=ctx,
                channel_id=guild_data[self.CHANNEL],
                message_id=guild_data[self.MESSAGE],
                title=guild_data[self.TITLE],
                combinations=guild_data[self.COMBINATIONS]
            )

        except InvalidArguments as error:
            await error.execute()
