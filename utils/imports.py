############################################# IMPORTS #############################################
#################### DISCORD ####################
from discord import (
    Emoji,
    Role,
    TextChannel
)
from discord.ext.commands import (
    Context,
    EmojiConverter,
    RoleConverter,
    TextChannelConverter
)
from discord.ext.commands import (
    BadArgument
)

##################### UTILS #####################
from utils.exceptions import InvalidArguments
from emoji import demojize
from typing import Union

############################################# GLOBALS #############################################

TextChannelType = Union[int, str, TextChannel]
EmojiType = Union[int, str, Emoji]
RoleType = Union[int, str, Role]

############################################ FUNCTIONS ############################################

async def import_channel(ctx: Context, channel: TextChannelType) -> TextChannel:
    try:
        return await TextChannelConverter().convert(ctx, str(channel))
    except BadArgument:
        raise InvalidArguments(
            ctx=ctx,
            title="Channel Error",
            message="Couldn't find provided channel"
        )

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

async def import_role(ctx: Context, role: RoleType) -> Role:
    try:
        return await RoleConverter().convert(ctx, str(role))
    except BadArgument:
        raise InvalidArguments(
            ctx=ctx,
            title="Role Error",
            message=f"Couldn't load {role} role"
        )
