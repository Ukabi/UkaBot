############################################# IMPORTS #############################################
#################### DISCORD ####################
from discord import (
    Embed,
    Emoji,
    File,
    Role
)
from discord.ext.commands import (
    BadArgument,
    Bot,
    Cog,
    Context,
    EmojiConverter,
    RoleConverter,
)
from discord.ext.commands import group

##################### DATA ######################
from .data import (
    PATH,
    EmojiTypes,
    RoleTypes
)

##################### UTILS #####################
from typing import Union
from utils.checks import (
    admin_or_permissions,
    ask_confirmation
)
from utils.exceptions import InvalidArguments

import io
import requests as rq

############################################### COGS ##############################################

class EmojiManager(Cog):

    ######################################### CONSTRUCTOR #########################################

    def __init__(self, bot: Bot):
        self.bot = bot

    #################################### EMOJI MANAGER COMMANDS ###################################

    @admin_or_permissions(manage_emojis=True)
    @group()
    async def emoji(self, ctx: Context):
        pass

    @admin_or_permissions(manage_emojis=True)
    @emoji.command()
    async def add(self, ctx: Context, file_path: str, name: str, *roles: RoleTypes):
        try:
            roles = [await RoleConverter().convert(ctx, str(role)) for role in roles]
        except BadArgument:
            error = InvalidArguments(
                ctx=ctx,
                title='Role Error',
                message="Provided roles could not be found"
            )
            await error.execute()

        else:
            if file_path.startswith("http"):
                req = rq.get(file_path)
                if req.ok:
                    byte_data = bytearray(req.content)
                    file = io.BytesIO(bytes(req.content))
                else:
                    error = InvalidArguments(
                        ctx=ctx,
                        title='Loading Error',
                        message="Couldn't retrieve picture from privided link"
                    )
                    await error.execute()

            else:
                try:
                    with open(f'{PATH}/{file_path}', 'rb') as image:
                        raw_data = image.read()
                except FileNotFoundError:
                    error = InvalidArguments(
                        ctx=ctx,
                        title='Loading Error',
                        message="Couldn't retrieve picture from privided path"
                    )
                    await error.execute()

                else:
                    byte_data = bytearray((raw_data))
                    file = io.BytesIO(bytes(byte_data))

            answer = await ask_confirmation(
                ctx=ctx,
                bot=self.bot,
                file=File(file, filename="emoji_template.png"),
                message=(
                    "Waiting for confirmation\n"
                    "Reply with y/n"
                )
            )
            if answer:
                emoji = await ctx.guild.create_custom_emoji(
                    name=name,
                    image=byte_data,
                    roles=roles
                )
                affected_roles = ", ".join([str(role) for role in roles]) if roles else "everyone"
                embed = Embed(
                    title=f"Successfully created {emoji} emoji",
                    description=f"Affected roles: {affected_roles}"
                )
            else:
                embed = Embed(
                    title="Cancelled"
                )

            await ctx.send(embed=embed)

    @admin_or_permissions(manage_emojis=True)
    @emoji.command()
    async def remove(self, ctx: Context, emoji: EmojiTypes):
        try:
            emoji = await EmojiConverter().convert(ctx, emoji)
        except BadArgument:
            error = InvalidArguments(
                ctx=ctx,
                title='Emoji Error',
                message="Provided emoji could not be found"
            )
            await error.execute()

        else:
            emoji_parse = str(emoji) if emoji.available else emoji.name
            answer = await ask_confirmation(
                ctx=ctx,
                bot=self.bot,
                message=(
                    f"Affected emoji: {emoji_parse}\n"
                    "Answer with y/n to confirm removal"
                )
            )
            if answer:
                await emoji.delete()
                embed = Embed(
                    title="Emoji Removed",
                    description=f"Successfully removed {emoji_parse} from server"
                )
            else:
                embed = Embed(
                    title="Cancelled"
                )

            await ctx.send(embed= embed)

    @admin_or_permissions(manage_emojis=True)
    @emoji.command(name='list')
    async def list_(self, ctx: Context):
        emojis = sorted(ctx.guild.emojis, key=lambda e: e.name)

        if emojis:
            message = "\n".join(self.emoji_infos(emoji) for emoji in emojis)
        else:
            message = "No emoji"

        embed = Embed(
            title="Server emojis list",
            description=message
        )
        await ctx.send(embed=embed)

    ######################################## STATIC METHODS #######################################

    @staticmethod
    def emoji_infos(emoji: Emoji) -> str:
        r = str(emoji) if emoji.available else emoji.name
        if emoji.managed:
            r += " - Twitch"
        elif emoji.roles:
            r += f' - Roles: {", ".join([str(role) for role in emoji.roles])}'
        return emoji
