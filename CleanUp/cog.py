from datetime import datetime, timedelta

from discord import (
    Member,
    Message,
    TextChannel
)
from discord import NotFound
from discord.errors import NotFound as NotFound_
from discord.ext.commands import (
    Bot,
    Cog,
    Context,
    MemberConverter
)
from discord.ext.commands import (
    bot_has_permissions,
    group,
    guild_only
)
from discord.ext.commands import BadArgument
from redbot.core.utils.mod import slow_deletion, mass_purge

from datetime import (
    datetime as dt,
    timedelta as td
)
from typing import (
    Callable,
    List,
    Set,
    Union
)

from utils import ask_confirmation
from utils.checks import admin_or_permissions

class Cleanup(Cog):

    def __init__(self, bot: Bot):
        super().__init__()
        self.bot = bot

    @staticmethod
    async def check_100_plus(ctx: Context, number: int) -> bool:
        check = await ask_confirmation(
            ctx=ctx,
            message=(
                f"You are going to delete {number} messages. Are you sure?\n"
                "Reply with {}/{}"
            ),
            conditions=("y", "n")
        )

        if check:
            return True
        else:
            await ctx.send("Cancelled")
            return False

    @staticmethod
    async def get_messages_for_deletion(
        *,
        channel: TextChannel,
        number: int = None,
        check: Callable[[Message], bool] = lambda x: True,
        limit: int = None,
        before: Union[Message, datetime] = None,
        after: Union[Message, datetime] = None,
        delete_pinned: bool = False,
    ) -> List[Message]:
        """
        Gets a list of messages meeting the requirements to be deleted.
        Generally, the requirements are:
        - We don't have the number of messages to be deleted already
        - The message passes a provided check (if no check is provided,
          this is automatically true)
        - The message is less than 14 days old
        - The message is not pinned

        Warning: Due to the way the API hands messages back in chunks,
        passing after and a number together is not advisable.
        If you need to accomplish this, you should filter messages on
        the entire applicable range, rather than use this utility.
        """

        # This isn't actually two weeks ago to allow some wiggle room on API limits
        two_weeks_ago = datetime.utcnow() - timedelta(days=14, minutes=-5)

        def message_filter(message):
            return (
                check(message)
                and message.created_at > two_weeks_ago
                and (delete_pinned or not message.pinned)
            )

        if after:
            if isinstance(after, Message):
                after = after.created_at
            after = max(after, two_weeks_ago)

        collected = []
        async for message in channel.history(
            limit=limit, before=before, after=after, oldest_first=False
        ):
            if message.created_at < two_weeks_ago:
                break
            if message_filter(message):
                collected.append(message)
                if number and number <= len(collected):
                    break

        return collected

    @group(name="cleanup")
    @admin_or_permissions(manage_messages=True)
    async def cleanup_group(self, ctx: Context):
        """Delete messages."""
        pass

    @cleanup_group.command(name="text")
    @guild_only()
    @bot_has_permissions(manage_messages=True)
    async def cleanup_text(self, ctx: Context, text: str, number: int, delete_pinned: bool = False):
        """Delete the last X messages matching the specified text.

        Example:
            `[p]cleanup text "test" 5`

        Remember to use double quotes.
        """
        channel = ctx.channel
        author = ctx.author

        if number > 100:
            cont = await self.check_100_plus(ctx, number)
            if not cont:
                return

        def check(m):
            if text in m.content:
                return True
            else:
                return False

        to_delete = await self.get_messages_for_deletion(
            channel=channel,
            number=number,
            check=check,
            before=ctx.message,
            delete_pinned=delete_pinned,
        )
        to_delete.append(ctx.message)

        reason = (
            f"{author.name}({author.id}) deleted {len(to_delete)} messages "
            f"containing '{text}' in channel {channel.id}."
        )
        print(reason)

        await mass_purge(to_delete, channel)

    @cleanup_group.command(name="user")
    @guild_only()
    @bot_has_permissions(manage_messages=True)
    async def cleanup_user(self, ctx: Context, user: str, number: int, delete_pinned: bool = False):
        """Delete the last X messages from a specified user.

        Examples:
            `[p]cleanup user @\u200bTwentysix 2`
            `[p]cleanup user Red 6`
        """
        channel = ctx.channel

        member = None
        try:
            member = await MemberConverter().convert(ctx, user)
        except BadArgument:
            try:
                _id = int(user)
            except ValueError:
                raise BadArgument()
                # TODO : Error Management

        _id = member.id
        author = ctx.author

        if number > 100:
            cont = await self.check_100_plus(ctx, number)
            if not cont:
                return

        def check(m):
            if m.author.id == _id:
                return True
            else:
                return False

        to_delete = await self.get_messages_for_deletion(
            channel=channel,
            number=number,
            check=check,
            before=ctx.message,
            delete_pinned=delete_pinned,
        )
        to_delete.append(ctx.message)

        reason = (
            f"{author.name}({author.id}) deleted {len(to_delete)} messages "
            f"made by {member or '???'}({_id}) in channel {channel.name}."
        )
        print(reason)

        await mass_purge(to_delete, channel)

    @cleanup_group.command(name="after")
    @guild_only()
    @bot_has_permissions(manage_messages=True)
    async def cleanup_after(self, ctx: Context, message_id: int, delete_pinned: bool = False):
        """Delete all messages after a specified message.

        To get a message id, enable developer mode in Discord's
        settings, 'appearance' tab. Then right click a message
        and copy its id.
        """
        channel = ctx.channel
        author = ctx.author

        try:
            after = await channel.fetch_message(message_id)
        except NotFound:
            await ctx.send("Message not found")
            return

        to_delete = await self.get_messages_for_deletion(
            channel=channel,
            number=None,
            after=after,
            delete_pinned=delete_pinned
        )

        reason = (
            f"{author.name}({author.id}) deleted {len(to_delete)} messages "
            f"in channel {channel.name}."
        )
        print(reason)

        await mass_purge(to_delete, channel)

    @cleanup_group.command(name="before")
    @guild_only()
    @bot_has_permissions(manage_messages=True)
    async def cleanup_before(
        self, ctx: Context, message_id: int, number: int, delete_pinned: bool = False
    ):
        """Deletes X messages before specified message.

        To get a message id, enable developer mode in Discord's
        settings, 'appearance' tab. Then right click a message
        and copy its id.
        """
        channel = ctx.channel
        author = ctx.author

        try:
            before = await channel.fetch_message(message_id)
        except NotFound:
            await ctx.send("Message not found")
            return

        to_delete = await self.get_messages_for_deletion(
            channel=channel,
            number=number,
            before=before,
            delete_pinned=delete_pinned
        )
        to_delete.append(ctx.message)

        reason = (
            f"{author.name}({author.id}) deleted {len(to_delete)} messages "
            f"in channel {channel.name}."
        )
        print(reason)

        await mass_purge(to_delete, channel)

    @cleanup.command(name="between")
    @guild_only()
    @bot_has_permissions(manage_messages=True)
    async def cleanup_between(self, ctx: Context, one: int, two: int, delete_pinned: bool = False):
        """Delete the messages between Messsage One and Message Two, providing the messages IDs.

        The first message ID should be the older message and the second one the newer.

        Example:
            `[p]cleanup between 123456789123456789 987654321987654321`
        """
        channel = ctx.channel
        author = ctx.author

        try:
            mone = await channel.fetch_message(one)
        except NotFound_:
            await ctx.send(f"Could not find a message with the ID of {one}.")
            return

        try:
            mtwo = await channel.fetch_message(two)
        except NotFound_:
            await ctx.send(f"Could not find a message with the ID of {two}.")
            return

        to_delete = await self.get_messages_for_deletion(
            channel=channel,
            after=mone,
            before=mtwo,
            delete_pinned=delete_pinned
        )
        to_delete.append(ctx.message)

        reason = (
            f"{author.name}({author.id}) deleted {len(to_delete)} messages "
            f"in channel {channel.name}."
        )
        print(reason)

        await mass_purge(to_delete, channel)

    @cleanup.command()
    @guild_only()
    @bot_has_permissions(manage_messages=True)
    async def cleanup_messages(self, ctx: Context, number: int, delete_pinned: bool = False):
        """Delete the last X messages.

        Example:
            `[p]cleanup messages 26`
        """
        channel = ctx.channel
        author = ctx.author

        if number > 100:
            cont = await self.check_100_plus(ctx, number)
            if not cont:
                return

        to_delete = await self.get_messages_for_deletion(
            channel=channel,
            before=ctx.message,
            delete_pinned=delete_pinned
        )
        to_delete.append(ctx.message)

        reason = (
            f"{author.name}({author.id}) deleted {len(to_delete)} messages "
            f"in channel {channel.name}."
        )
        print(reason)

        await mass_purge(to_delete, channel)

    @cleanup.command(name="bot")
    async def cleanup_bot(
        self, ctx: Context, number: int, match_pattern: str = None, delete_pinned: bool = False
    ):
        """Clean up messages owned by the bot.

        By default, all messages are cleaned. If a third argument is specified,
        it is used for pattern matching - only messages containing the given text will be deleted.
        """
        channel = ctx.channel
        author = ctx.message.author

        if number > 100:
            cont = await self.check_100_plus(ctx, number)
            if not cont:
                return

        can_mass_purge = False
        if type(author) is Member:
            me = ctx.guild.me
            can_mass_purge = channel.permissions_for(me).manage_messages

        if match_pattern:
            def content_match(c):
                return match_pattern in c
        else:
            def content_match(_):
                return True

        def check(m):
            if m.author.id == self.bot.user.id and content_match(m.content):
                return True
            else:
                return False

        to_delete = await self.get_messages_for_deletion(
            channel=channel,
            number=number,
            check=check,
            before=ctx.message,
            delete_pinned=delete_pinned
        )

        if ctx.guild:
            channel_name = "channel " + channel.name
        else:
            channel_name = str(channel)

        reason = (
            f"{author.name}({author.id}) deleted {len(to_delete)} messages "
            f"sent by the bot in channel {channel.name}."
        )
        print(reason)

        if can_mass_purge:
            await mass_purge(to_delete, channel)
        else:
            await slow_deletion(to_delete)
