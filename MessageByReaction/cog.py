############################################# IMPORTS #############################################
#################### DISCORD ####################
from discord import (
    Embed,
    Emoji,
    Guild,
    Message,
    TextChannel,
    RawReactionActionEvent,
    Reaction
)
from discord import NotFound
from discord.ext.commands import (
    Bot,
    Cog,
    Context
)
from discord.ext.commands import group

##################### DATA ######################
from .data import (
    Combination,
    Guild as GuildData
)

##################### UTILS #####################
from typing import (
    Awaitable,
    List,
    Union
)
from utils import (
    TextChannelType,
    Config as Cfg,
    EmojiType,
    ImprovedList
)
from utils import (
    add_reactions,
    import_channel,
    import_emoji
)
from utils.checks import (
    admin,
    admin_or_permissions,
    ask_confirmation,
)
from utils.exceptions import InvalidArguments

############################################### COGS ##############################################

class MessageByReaction(Cog):

    ######################################### CONSTRUCTOR #########################################

    def __init__(self, bot: Bot):
        self.bot = bot
        self.config = Cfg(self)

        self.defaults = GuildData(
            channel=0,
            combinations=[],
            message=0,
            title="React with corresponding emoji to send message"
        )
        self.config.defaults_guild(self.defaults)

        print("MESSAGE_BY_REACTION COG: loaded")

    ########################################### UNLOADER ##########################################

    def cog_unload(self):
        del self

        print("MESSAGE_BY_REACTION COG: unloaded")

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
    async def mbr(self, ctx: Context):
        pass

    @admin()
    @mbr.command()
    async def title(self, ctx: Context, *, title: str):
        guild_config = self.config.guild(ctx.guild)
        guild_data = guild_config.get()

        guild_data.title = title
        try:
            await self._edit_message(ctx, guild_data)
        except InvalidArguments:
            pass

        guild_config.set(guild_data)

        embed = Embed(
            title='Title Changed',
            description=f'Successfully updated title to {title}'
        )
        await ctx.send(embed=embed)

    @admin_or_permissions(manage_roles=True)
    @mbr.command()
    async def add(self, ctx: Context, emoji: EmojiType, channel: TextChannelType, *, message: str):
        guild = ctx.guild
        guild_config = self.config.guild(guild)
        guild_data = guild_config.get()

        combinations = guild_data.combinations

        try:
            emoji = await import_emoji(ctx, emoji)
            emoji_id = emoji.id if isinstance(emoji, Emoji) else emoji
            if emoji_id in [c.emoji for c in combinations]:
                raise InvalidArguments(
                    ctx=ctx,
                    title="Emoji Error",
                    message=f"Emoji {emoji} already used"
                )

            channel = await import_channel(ctx, channel)

        except InvalidArguments as error:
            await error.execute()

        else:
            new = Combination(
                channel=channel.id,
                emoji=emoji.id if hasattr(emoji, "id") else emoji,
                message=message
            )
            combinations.append(new)

            guild_data.combinations = combinations
            try:
                await self._edit_message(ctx, guild_data)
            except InvalidArguments:
                pass

            guild_config.set(guild_data)

            embed = Embed(
                title="Combination Added",
                description=f"{emoji} successfully linked with {channel.mention}: {message}"
            )
            await ctx.send(embed=embed)

    @admin_or_permissions(manage_roles=True)
    @mbr.command()
    async def remove(self, ctx: Context, *, emoji: EmojiType):
        guild = ctx.guild
        guild_config = self.config.guild(guild)
        guild_data = guild_config.get()

        combinations = guild_data.combinations

        try:
            emoji = await import_emoji(ctx, emoji)
            emoji_id = emoji.id if isinstance(emoji, Emoji) else emoji
            if emoji_id not in [c.emoji for c in combinations]:
                raise InvalidArguments(
                    ctx=ctx,
                    message="Argument wasn't found in data"
                )

        except InvalidArguments as error:
            await error.execute()

        else:
            for combination in combinations:
                if combination.emoji == emoji_id:
                    combinations.remove(combination)
                    break

            guild_data.combinations = combinations
            try:
                await self._edit_message(ctx, guild_data)
            except InvalidArguments:
                pass

            guild_config.set(guild_data)

            embed = Embed(
                title="Combination Removed",
                description=f"{emoji} successfully unlinked"
            )
            await ctx.send(embed=embed)

    @admin()
    @mbr.command()
    async def create(self, ctx: Context):
        guild = ctx.guild
        guild_config = self.config.guild(guild)
        guild_data = guild_config.get()

        embed = self._message_content(ctx, guild_data)
        message = await ctx.send(embed=embed)
        await add_reactions(
            ctx=ctx,
            message=message,
            emojis=[c.emoji for c in guild_data.combinations]
        )

        guild_data.channel = message.channel.id
        guild_data.message = message.id
        guild_config.set(guild_data)

    @admin()
    @mbr.command()
    async def message(self, ctx: Context, channel_id: int, message_id: int):
        guild = ctx.guild
        guild_config = self.config.guild(guild)
        guild_data = guild_config.get()

        guild_data.channel = channel_id
        guild_data.message = message_id
        try:
            message = await self._edit_message(ctx, guild_data)
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
    @mbr.command()
    async def show(self, ctx: Context):
        guild = ctx.guild
        guild_config = self.config.guild(guild)
        guild_data = guild_config.get()

        guild_data.title = "Message By Reaction Template"

        embed = self._message_content(ctx, guild_data)
        await ctx.send(embed=embed)

    @admin()
    @mbr.command()
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
    @mbr.command()
    async def update(self, ctx: Context):
        guild = ctx.guild
        guild_config = self.config.guild(guild)
        guild_data = guild_config.get()

        try:
            await self._edit_message(ctx, guild_data)
        except InvalidArguments as error:
            await error.execute()

    ######################################## CLASS METHODS ########################################

    @classmethod
    async def _edit_message(cls, ctx: Context, guild_data: GuildData) -> Message:
        guild = ctx.guild
        channel_id = guild_data.channel
        message_id = guild_data.message
        combinations = guild_data.combinations

        message = await cls._find_message(guild, guild_data, ctx)
        if message.author.id == ctx.me.id:
            embed = cls._message_content(ctx, guild_data)
            await message.edit(embed=embed)
            await add_reactions(
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
    async def _treat_reaction(
        cls, guild: Guild, guild_data: GuildData, payload: RawReactionActionEvent
    ):
        message_id = guild_data.message
        if payload.message_id == message_id and payload.user_id != guild.me.id:
            combinations = guild_data.combinations

            emoji = payload.emoji
            combination = ImprovedList(combinations).get_item(
                emoji.id if emoji.id else str(emoji),
                key=lambda c: c.emoji
            )

            channel = guild.get_channel(combination.channel)
            if channel:
                method = cls._get_method(
                    channel=channel,
                    event_type=payload.event_type
                )
                await method(combination.message)

    ####################################### STATIC METHODS ########################################

    @staticmethod
    async def _find_message(guild: Guild, guild_data: GuildData, ctx: Context = None) -> Message:
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
    def _get_method(channel: TextChannel, event_type: str) -> Awaitable:
        if event_type == "REACTION_ADD":
            async def method(message: str):
                await channel.send(message)

        else:
            async def method(message: str):
                return

        return method

    @staticmethod
    def _message_content(ctx: Context, guild_data: GuildData) -> Embed:
        title = guild_data.title
        combinations = guild_data.combinations

        if combinations:
            content = ""
            for combination in combinations:
                emoji = combination.emoji
                try:
                    emoji = ImprovedList(ctx.bot.emojis).get_item(
                        emoji,
                        key=lambda e: e.id
                    )
                except ValueError:
                    pass

                channel = combination.channel
                try:
                    channel = ImprovedList(ctx.guild.channels).get_item(
                        channel,
                        key=lambda c: c.id
                    )
                    channel = channel.mention
                except ValueError:
                    pass

                content += f"{emoji} - {channel}: {combination.message}" + "\n"

        else:
            content = "No combination registered yet"

        return Embed(
            title=title,
            description=content
        )
