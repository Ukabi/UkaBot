############################################# IMPORTS #############################################

#################### DISCORD ####################
from discord import (
    Embed,
    Guild,
    Message,
    Member,
    Reaction,
    TextChannel,
    User
)
from discord.abc import GuildChannel
from discord.ext import tasks
from discord.ext.commands import (
    BadArgument,
    Bot,
    Cog,
    Context,
    EmojiConverter,
    MemberConverter,
)
from discord.ext.commands import group

##################### UTILS #####################
import re
import time

from datetime import datetime as dt
from emoji import (
    demojize,
    emojize
)
from typing import Dict, List, Union
from utils import Config as Cfg
from utils import (
    admin,
    ask_confirmation,
    get,
    update_config
)
from utils.exceptions import InvalidArguments

############################################### COGS ##############################################

class EmojiData(Cog):
    FIND_CUSTOM_EMOJIS = re.compile("(?<=<:)\w+:\d+(?=>)").findall
    FIND_EMOJIS = re.compile("(?<=:)\w+(?=:)").findall               # For Alias, not supported yet
    VERIFY_EMOJI = re.compile("<:\w+:\d+>").match

    APPEND = 1
    REMOVE = -1

    ALIASES = "aliases"                                              # For Alias, not supported yet
    COUNT = "count"
    DATA = "data"
    LAST_CHECKED = "last_checked"
    NAME = "name"

    ######################################### CONSTRUCTOR #########################################

    def __init__(self, bot: Bot):
        self.bot = bot
        self.config = Cfg(self)

        self.default_guild = {
            self.ALIASES: {},                                        # For Alias, not supported yet
            self.DATA: {},
            self.LAST_CHECKED: 1420066800.0,
        }
        self.config.defaults_guild(self.default_guild)

        self.default_member = {}
        self.config.defaults_member(self.default_member)

        self.scheduler.start()

    @tasks.loop(hours=1)
    async def scheduler(self):
        #TODO: ALL_STUFF SUPPORT IN Config LIBRARY
        #guilds = self.config.all_guilds()

        #for guild_id, guild_data in guilds.items():
        #    guild = self.bot.get_guild(guild_id)
        #    if guild:
        #        await self.treat_guild(
        #            guild=guild,
        #            last_checked=guild_data[self.LAST_CHECKED]
        #        )

        #        self.update_check(guild)
        pass

    @scheduler.before_loop
    async def before_scheduler(self):
        await self.bot.wait_until_ready()

    @scheduler.after_loop
    async def after_scheduler(self):
        self.scheduler.stop()

    ########################################### UNLOADER ##########################################

    def cog_unload(self):
        self.scheduler.cancel()

    ############################################# CORE ############################################

    def update_check(self, guild: Guild):
        update_config(
            config=self.config.guild(guild),
            attribute=self.LAST_CHECKED,
            value=dt.utcnow().timestamp()
        )

    def update_data(
        self, data: Dict[str, Dict[str, Union[str, int]]],
        emoji_ref: Union[int, str], emoji_name: str, treat_type: int = 0
    ):
        emoji_data = data.get(str(emoji_ref), {self.NAME: emoji_name, self.COUNT: 0})
        emoji_data[self.COUNT] += treat_type
        data[emoji_ref] = emoji_data

    async def treat_reactions(
        self, reactions: List[Reaction], treat_type: int = 0
    ):
        for reaction in reactions:
            async for user in reaction.users():
                self.treat_reaction(reaction, user, treat_type)

    def treat_reaction(
        self, reaction: Reaction, member: Union[Member, User], treat_type: int = 0
    ):
        if member.bot:                                              # Excluding bot from statistics
            return

        emoji = reaction.emoji
        if reaction.custom_emoji:
            ref = emoji.id
            name = emoji.name
        else:
            ref = demojize(emoji).replace(":", "")
            name = ref

        print(f"reaction: {reaction.message.created_at.isoformat(sep=' ')} {name}")

        guild_config = self.config.guild(reaction.message.channel.guild)
        guild_data = guild_config.get()
        self.update_data(
            data=guild_data[self.DATA],
            emoji_ref=ref,
            emoji_name=name,
            treat_type=treat_type,
        )
        guild_config.set(guild_data)

        if isinstance(member, Member):
            member_config = self.config.member(member)
            member_data = member_config.get()
            self.update_data(
                data=member_data,
                emoji_ref=ref,
                emoji_name=name,
                treat_type=treat_type
            )
            member_config.set(member_data)

    def treat_message(self, message: Message, treat_type: int = 0):
        member = message.author

        if member.bot:                                              # Excluding bot from statistics
            return

        elif isinstance(message.channel, TextChannel):
            text = message.content
            custom_emojis = self.FIND_CUSTOM_EMOJIS(text)
            custom_emojis = [e.split(":") for e in custom_emojis]

            text = demojize(text)
            casual_emojis = self.FIND_EMOJIS(text)
            casual_emojis = [e for e in casual_emojis if f":{e}:" != emojize(f":{e}:")]
            casual_emojis = [[e, e] for e in casual_emojis]

            emojis = custom_emojis + casual_emojis

            guild_config = self.config.guild(message.channel.guild)
            guild_data = guild_config.get()
            if isinstance(member, Member):
                member_config = self.config.member(member)
                member_data = member_config.get()

            print(f"message: {message.created_at.isoformat(sep=' ')} ", end=" ")
            for name, ref in emojis:
                print(name, end=" ")
                self.update_data(
                    data=guild_data[self.DATA],
                    emoji_ref=ref,
                    emoji_name=name,
                    treat_type=treat_type,
                )
                if isinstance(member, Member):
                    self.update_data(
                        data=member_data,
                        emoji_ref=ref,
                        emoji_name=name,
                        treat_type=treat_type,
                    )
            print("")

            guild_config.set(guild_data)
            if isinstance(member, Member):
                member_config.set(member_data)

    async def treat_channel(
        self, channel: TextChannel, after: dt = dt.fromtimestamp(1420066800.0),
        stop: dt = None, treat_type: int = 0, count_total: int = 0,
        count_channels: List[TextChannel] = [], progress_message: Message = None
    ) -> List[int]:

        count_channel = 0
        async for message in channel.history(limit=None, after=after, before=stop):
            self.treat_message(
                message=message,
                treat_type=treat_type
            )
            await self.treat_reactions(
                reactions=message.reactions,
                treat_type=treat_type
            )

            count_channel += 1
            count_total += 1
            if progress_message and not count_total % 100:
                await self.edit_progress_message(
                    channel=channel,
                    count_channel=count_channel,
                    count_total=count_total,
                    count_channels=count_channels,
                    progress_message=progress_message,
                )

        print((
            f"Processed {channel.name} from {channel.guild.name} - "
            f"Channel: {count_channel} - Guild: {count_total}"
        ))

        return count_total, count_channel

    async def treat_guild(
        self, guild: Guild, last_checked: float = 1420066800.0, stop: dt = None,
        treat_type: int = 0, progress_channel: TextChannel = None
    ):
        if progress_channel:
            embed = Embed(
                title="Count Progress",
                description=""
            )
            progress_message = await progress_channel.send(embed=embed)
        else:
            progress_message = None

        after = dt.fromtimestamp(last_checked)
        count_total = 0
        count_channels = []
        for channel in guild.text_channels:
            count_total, count_channel = await self.treat_channel(
                channel=channel,
                after=after,
                stop=stop,
                count_channels=count_channels,
                count_total=count_total,
                progress_message=progress_message,
                treat_type=treat_type,
            )
            count_channels.append((str(channel), count_channel))

    async def edit_progress_message(
        self, progress_message: Message, channel: TextChannel, count_channel: int,
        count_total: int, count_channels: List[TextChannel]
    ):
        edit = (
            "\n".join([" - ".join([str(val) for val in chan]) for chan in count_channels]) + "\n"
            f"{channel.name} process: {count_channel}" + "\n"
            "\n"
            f"Total processed message: {count_total}"
        )
        embed = Embed(
            title="Count progress",
            description=edit
        )
        await progress_message.edit(embed=embed)

    ############################################ EVENTS ###########################################

    @Cog.listener()
    async def on_message(self, message: Message):
        try:
            guild = message.channel.guild
        except AttributeError:
            return

        self.treat_message(
            message=message,
            treat_type=self.APPEND
        )

        self.update_check(guild)

    @Cog.listener()
    async def on_message_delete(self, message: Message):
        try:
            guild = message.channel.guild
        except AttributeError:
            pass

        self.treat_message(
            message=message,
            treat_type=self.REMOVE
        )
        await self.treat_reactions(
            reactions=message.reactions,
            treat_type=self.REMOVE
        )

        self.update_check(guild)

    @Cog.listener()
    async def on_bulk_message_delete(self, messages: List[Message]):
        guilds = []
        for message in messages:
            try:
                guilds.append(message.channel.guild)
            except AttributeError:
                guilds.append(None)

        for guild, message in zip(guilds, messages):
            if guild:
                self.treat_message(
                    message=message,
                    treat_type=self.REMOVE
                )
                await self.treat_reactions(
                    reactions=message.reactions,
                    treat_type=self.REMOVE
                )

                self.update_check(guild)

    @Cog.listener()
    async def on_message_edit(self, before: Message, after: Message):
        try:
            guild = before.channel.guild
        except AttributeError:
            return

        self.treat_message(
            message=before,
            treat_type=self.REMOVE
        )
        self.treat_message(
            message=after,
            treat_type=self.APPEND
        )

        self.update_check(guild)

    @Cog.listener()
    async def on_reaction_add(
        self, reaction: Reaction, member: Union[Member, User]
    ):
        try:
            guild = reaction.message.channel.guild
        except AttributeError:
            return

        self.treat_reaction(
            reaction=reaction,
            member=member,
            treat_type=self.APPEND
        )

        self.update_check(guild)

    @Cog.listener()
    async def on_reaction_remove(
        self, reaction: Reaction, member: Union[Member, User]
    ):
        try:
            guild = reaction.message.channel.guild
        except AttributeError:
            return

        self.treat_reaction(
            reaction=reaction,
            member=member,
            treat_type=self.REMOVE
        )

        self.update_check(guild)

    @Cog.listener()
    async def on_reaction_clear(self, reactions: List[Reaction]):
        try:
            guild = reactions[0].message.channel.guild
        except AttributeError or IndexError:
            return

        await self.treat_reactions(
            reactions=reactions,
            treat_type=self.REMOVE
        )

        self.update_check(guild)

    @Cog.listener()
    async def on_guild_channel_delete(self, channel: GuildChannel):
        guild = channel.guild

        if isinstance(channel, TextChannel):
            await self.treat_channel(
                channel=channel,
                treat_type=self.REMOVE
            )

            self.update_check(guild)

    @Cog.listener()
    async def on_guild_join(self, guild: Guild):
        await self.treat_guild(
            guild=guild,
            stop=dt.utcnow(),
            treat_type=self.APPEND
        )

        self.update_check(guild)

    ######################################## STAT COMMANDS ########################################

    @group(name="emojidata")
    async def emojidata_group(self, ctx: Context):
        pass

    @admin()
    @emojidata_group.command(name="reset")
    async def emojidata_reset(self, ctx: Context):
        """ : resets the emoji data list."""
        answer = await ask_confirmation(
            ctx=ctx,
            bot=self.bot
        )
        if answer:
            guild = ctx.guild

            self.config.guild(guild).set(self.default_guild)
            self.config.clear_all_members(guild)

            embed = Embed(
                title="Data Reset",
                description="Now making fresh data"
            )
            await ctx.send(embed=embed)

            await self.treat_guild(
                guild=guild,
                stop=dt.utcnow(),
                treat_type=self.APPEND,
                progress_channel=ctx.channel
            )

        else:
            embed = Embed(
                title="Cancelled"
            )
            await ctx.send(embed=embed)

    @emojidata_group.command(name="guild")
    async def emojidata_guild(self, ctx: Context, top: int = 10):
        """**(top=10)** : shows guild emoji data."""
        try:
            top = int(top)
        except ValueError:
            error = InvalidArguments(
                ctx=ctx,
                message="Invalid top value"
            )

            await error.execute()

        guild = ctx.guild

        data = self.config.guild(guild).get()[self.DATA]

        embed = await self.make_message(
            ctx=ctx,
            raw_data=data,
            top=int(top),
            title=f"Emoji stats for {guild.name}"
        )

        await ctx.send(embed=embed)

    @emojidata_group.command(name="member")
    async def emojidata_member(
        self, ctx: Context, member: str = "", top: int = 10
    ):
        """**(member) (top=10)** : shows member emoji data."""
        try:
            member = await MemberConverter().convert(ctx, member)
        except BadArgument or TypeError:
            try:
                top = int(member) if int(member) < 100 else top
            except ValueError:
                pass
            member = ctx.author

        data = self.config.member(member).get()

        embed = await self.make_message(
            ctx=ctx,
            raw_data=data,
            top=top,
            title=f"Emoji stats for {member}"
        )

        await ctx.send(embed=embed)

    async def make_message(
        self, ctx: Context, top: int, title: str,
        raw_data: Dict[str, Dict[str, int]]
    ):
        data = [(key, val[self.NAME], val[self.COUNT]) for key, val in raw_data.items()]
        data.sort(key=lambda x: x[2], reverse=True)

        top = 25 if top > 25 else top
        top = len(data) if len(data) < top else top

        if data:
            message = ""
            for emoji_id, emoji_name, count in data[:top]:
                try:
                    e = await EmojiConverter().convert(ctx, emoji_id)
                    if not e.is_usable():
                        e = e.name
                except BadArgument:
                    if f":{emoji_name}:" != emojize(f":{emoji_name}:", ):
                        e = emojize(f":{emoji_name}:")
                    else:
                        e = emoji_name
                message += f"{e} - {count}\n"

        else:
            message = "No emoji data"

        return Embed(
            title=title,
            description=message
        )

    ####################################### ALIAS COMMANDS ########################################
    """
    def sum_alias_to_main_data(self, data: dict, main_emoji_name: str, main_emoji_id: int,
                               alias_emoji_id: int):
        count = 'count'

        main_emoji_data = data.pop(main_emoji_id, {count: 0})
        alias_emoji_data = data.pop(alias_emoji_id, {count: 0})

        if main_emoji_data[count] or alias_emoji_data[count]:
            temp = {'name': main_emoji_name}
            temp[count] = main_emoji_data[count] + alias_emoji_data[count]
            data[main_emoji_id] = temp

        return data

    @admin()
    @emojidata_group.group(name='alias')
    async def emojidata_alias(self, ctx: Context):
        pass

    @admin()
    @emojidata_alias.command(name='add')
    async def emojidata_alias_add(self, ctx: Context, main_emoji: str, alias_emoji: str):
        if self.verify_emoji(main_emoji) and self.verify_emoji(alias_emoji):
            guild = ctx.guild

            aliases = await self.config.guild(guild).aliases()

            main_emoji_id = self.get_id_custom_emoji(main_emoji)
            alias_emoji_id = self.get_id_custom_emoji(alias_emoji)

            if alias_emoji_id in list(aliases.values()) + list(aliases.keys()):
                if alias_emoji_id in aliases.keys():
                    type_ = "an alias"
                else:
                    type_ = "a main"

                embed = Embed(
                    title="Error",
                    color=COLOR,
                    description="Alias already registered as {}.".format(type_)
                )

            else:
                aliases[alias_emoji_id] = main_emoji_id
                await self.config.guild(guild).aliases.set(aliases)

                aliases_names = await self.config.guild(guild).aliases_names()

                main_emoji_name = self.get_name_custom_emoji(main_emoji)
                aliases_names[main_emoji_name] = (main_emoji_id, False)

                alias_emoji_name = self.get_name_custom_emoji(alias_emoji)
                aliases_names[alias_emoji_name] = (alias_emoji_id, True)

                await self.config.guild(guild).aliases_names.set(aliases_names)

                 count = 'count'

                guild_data = await self.config.guild(guild).data()
                guild_data = self.sum_alias_to_main_data(
                    guild_data,
                    main_emoji_name,
                    main_emoji_id,
                    alias_emoji_id
                )

                await self.config.guild(guild).data.set(guild_data)

                members = await self.config.all_members(guild)
                for member_keys in members.values():
                    member_data = member_keys['data']
                    member_data = self.sum_alias_to_main_data(
                        member_data,
                        main_emoji_name,
                        main_emoji_id,
                        alias_emoji_id
                    )

                await self.config.all_members(guild).set(members)

                embed = Embed(
                    title="Alias set!",
                    color=COLOR,
                    description="Alias emoji data will now"
                                "be summed with main emoji data."
                )

        else:
            embed = Embed(
                title="Error",
                color=COLOR,
                description="Arguments aren't custom emojis."
            )

        await ctx.send(embed=embed)

    @admin()
    @emojidata_alias.command(name='remove')
    async def emojidata_alias_remove(self, ctx: Context, emoji: str):
        guild = ctx.guild

        aliases_names = await self.config.guild(guild).aliases_names()
        if self.verify_emoji(emoji):
            emoji_name = self.get_name_custom_emoji(emoji)
            emoji_id = self.get_id_custom_emoji(emoji)
            emoji_data = aliases_names.get(emoji_name, None)
            if emoji_id not in emoji_data:
                emoji_data = None
        else:
            emoji_name = emoji
            emoji_data = aliases_names.get(emoji_name, None)

        if emoji_data:
            aliases = await self.config.guild(guild).aliases()
            emoji_id, is_alias = emoji_data

            if is_alias:
                aliases.pop(emoji_id)
            else:
                to_remove = list()
                for alias_id, main_id in aliases.items():
                    if emoji_id == main_id:
                        to_remove.append(alias_id)
                [aliases.pop(alias_id) for alias_id in to_remove]

            await self.config.guild(guild).aliases.set(aliases)

        else:
            embed = Embed(
                title="Error",
                color=COLOR,
                description="Argument isn't an already assigned custom emoji."
                            "The aliases might require a reset if emoji isn't"
                            "available anymore."
            )

    @mod()
    @emojidata_alias.command(name='list')
    async def emojidata_alias_list(self, ctx: Context):
        guild = ctx.guild
        aliases_by_alias = await self.config.guild(guild).aliases()
        aliases_names_by_name = await self.config.guild(guild).aliases_names()

        main_emojis_ids = list(set(aliases_by_alias.values()))

        aliases_by_main = dict()
        for main_emoji_id in main_emojis_ids:
            aliases = list()
            for alias, main in aliases_by_alias.items():
                if main_emoji_id == main:
                    aliases.append(alias)
            aliases_by_main[main_emoji_id] = aliases

        emojis_ids = set()
        for emoji_id, is_alias in aliases_names_by_name.values():
            emojis_ids = emojis_ids.union(emoji_id)

        aliases_names_by_id = dict()
        for emoji_id in emojis_ids:
            names = list()
            for name, data in aliases_names_by_name.items():
                if data[0] == emoji_id:
                    names.append(name)
            aliases_names_by_id[emoji_id] = names[0]

        aliases = dict()
        for main, alias in aliases_by_main.items():
            main = self.import_emoji(
                ctx.guild,
                main,
                aliases_names_by_id
            )
            main = temp_main if temp_main else None

    @admin()
    @emojidata_alias.command(name='reset')
    async def emojidata_alias_reset(self, ctx: Context):
        await ask_reset(
            bot=self.bot,
            ctx=ctx,
            res_func=(
                self.config.guild(ctx.guild).aliases.clear,
                self.config.guild(ctx.guild).aliases_names.clear
            ),
            obj="Guild emoji data list",
            message="Write y/n to confirm reset"
        )

    def import_emoji(self, guild: Guild, emoji_id: int, replacement_name: str):
        e = get_emoji(guild, emoji_id)
        if e is None:
            e = replacement_name
        return e
    """
