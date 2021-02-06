############################################# IMPORTS #############################################

#################### DISCORD ####################
from discord import (
    Embed,
    Emoji,
    File,
    Role,
    TextChannel
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

##################### UTILS #####################
import io
import requests as rq

from pathlib import Path
from typing import (
    List,
    Union
)
from utils import InvalidArguments
from utils import (
    admin_or_permissions,
    ask_confirmation
)

############################################### COGS ##############################################

class EmojiManager(Cog):
    PATH = f'{Path(__file__).absolute()}/emojis'

    ######################################### CONSTRUCTOR #########################################

    def __init__(self, bot: Bot):
        self.bot = bot

    #################################### EMOJI MANAGER COMMANDS ###################################

    @admin_or_permissions(manage_emojis=True)
    @group(name='emoji')
    async def emoji_group(self, ctx: Context):
        pass

    @admin_or_permissions(manage_emojis=True)
    @emoji_group.command(name='add')
    async def emoji_add(self, ctx: Context, file_path: str, name: str, *roles: List[Union[int, str, Role]]):
        """
        **[file] [name] (roles)** : adds an emoji to the server,
        if roles, restricts it for precised roles.
        """
        try:
            roles = [await RoleConverter().convert(ctx, role) for role in roles]
        except BadArgument:
            error = InvalidArguments(
                ctx,
                title='Role Error',
                message="Provided roles could not be found"
            )
            await error.execute()
            return

        if file_path.startswith("http"):
            req = rq.get(file_path)
            if req.ok:
                byte_data = bytearray(req.content)
                file = io.BytesIO(bytes(req.content))
            else:
                error = InvalidArguments(
                    ctx,
                    title='Loading Error',
                    message="Couldn't retrieve picture from privided link"
                )
                await error.execute()
                return

        else:
            try:
                with open(f'{self.PATH}/{file_path}', 'rb') as image:
                    raw_data = image.read()
                    byte_data = bytearray((raw_data))
                    file = io.BytesIO(bytes(byte_data))
            except FileNotFoundError:
                error = InvalidArguments(
                    ctx,
                    title='Loading Error',
                    message="Couldn't retrieve picture from privided path"
                )
                await error.execute()
                return

        answer = await ask_confirmation(
            ctx=ctx,
            bot=self.bot,
            pic=File(file, filename="emoji_template.png"),
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
                title=f"Successfully created {emoji} emoji.",
                description=f"Affected roles: {affected_roles}."
            )
        else:
            embed = Embed(
                title="Cancelled"
            )

        await ctx.send(embed=embed)

    @admin_or_permissions(manage_emojis=True)
    @emoji_group.command(name='remove')
    async def emoji_remove(self, ctx: cmd.Context, emoji: Union[str, int, Emoji]):
        """**[emoji]** : removes emoji from server."""
        try:
            emoji = await EmojiConverter().convert(ctx, emoji)
            emoji_parse = str(emoji) if emoji.available else emoji.name
        except BadArgument:
            error = InvalidArguments(
                ctx,
                title='Emoji Error',
                message="Provided emoji could not be found"
            )
            await error.execute()
            return

        answer = await ask_confirmation(
            ctx=ctx,
            bot=self.bot,
            message=(
                f"Affected emoji: {emoji_parse}\n"
                "Answer with y/n to confirm removal."
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
    @emoji_group.command(name='list')
    async def emoji_list(self, ctx: Context):
        """: shows the server's emoji list."""
        emojis = ctx.guild.emojis

        if not emojis:
            message = "No emoji"
        else:
            for emoji in emojis:
                message += str(emoji) if emoji.available else emoji.name
                if emoji.managed:
                    message += " - Twitch"
                elif emoji.roles:
                    message += f' - Roles: {", ".join([str(role) for role in emoji.roles])}'
                message += "\n"

        embed = Embed(
            title="Server emojis list",
            description=message
        )
        await ctx.send(embed=embed)