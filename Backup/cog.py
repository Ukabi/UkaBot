############################################# IMPORTS #############################################

#################### DISCORD ####################
from discord import (
    Embed,
    Guild,
    Message,
    TextChannel,
    HTTPException,
    NotFound
)
from discord.ext.commands import (
    Bot,
    Cog,
    Context
)
from discord.ext.commands import group

##################### DATA ######################
from .data import (
    Message as MessageData,
    Channel as ChannelData,
    Reaction as ReactionData
)

##################### UTILS #####################
import os
from typing import (
    List,
    Tuple
)
from utils import (
    Config as Cfg,
    Group
)

############################################### COGS ##############################################

class Backup(Cog):

    ######################################### CONSTRUCTOR #########################################

    def __init__(self, bot: Bot):
        self.bot = bot
        self.config = Cfg(self)

        self.defaults = ChannelData([])
        self.config.defaults_channel(self.defaults)

    ########################################### UNLOADER ##########################################

    def cog_unload(self):
        del self

    ############################################# CORE ############################################

    async def edit_progress_message(
        self, channel: TextChannel, count_channels: List[Tuple[str, int]],
        count_total: int, count_channel: int, progress_message: Message
    ):
        message = ""

        for c_name, c_count in count_channels: # parsing history
            message += f"{c_name} - {c_count}" + "\n"

        # current
        message += f"{channel.name} process: {count_channel}" + "\n"
        message += "\n"
        message += f"Total processed messages: {count_total}"

        embed = Embed(
            title="Count progress",
            description=message
        )
        await progress_message.edit(embed=embed)

    async def treat_guild(self, guild: Guild, progress_channel: TextChannel = None):
        if progress_channel:
            embed = Embed(
                title="Count Progress",
                description=""
            )
            progress_message = await progress_channel.send(embed=embed)
        else:
            progress_message = None

        count_total = 0
        count_channels: List[Tuple[str, int]] = []

        for channel in guild.text_channels:
            count_total, count_channel = await self.treat_channel(
                channel=channel,
                count_channels=count_channels,
                count_total=count_total,
                progress_message=progress_message
            )
            count_channels.append((str(channel), count_channel))
    
    async def treat_channel(
        self, channel: TextChannel, count_channels: List[Tuple[str, int]],
        count_total: int, progress_message: Message = None
    ) -> Tuple[int, int]:
        channel_config = self.config.channel(channel)
        
        count_channel = 0
        async for message in channel.history(limit=None):
            await self.treat_message(message, channel_config)

            count_channel += 1
            count_total += 1
            if progress_message and not count_total % 100:
                await self.edit_progress_message(
                    progress_message=progress_message,
                    channel=channel,
                    count_channel=count_channel,
                    count_channels=count_channels,
                    count_total=count_total
                )
        
        channel_config.set(channel_config.get()) # saving parse

        return count_total, count_channel
    
    async def treat_message(self, message: Message, channel_config: Group):
        channel = str(message.channel)
        date = message.created_at.timestamp()
        member = str(message.author)
        text = message.content
        reactions = await self.treat_reactions(message)
        attachments = await self.treat_attachements(
            message,
            channel_config.file.removesuffix(".json")
        )

        to_add = MessageData(
            date=date,
            channel=channel,
            member=member,
            text=text,
            reactions=reactions,
            attachments=attachments
        )

        channel_data = channel_config.get()
        channel_data.data.append(to_add)
    
    async def treat_reactions(self, message: Message) -> List[ReactionData]:
        to_add: List[Tuple[str, List[str]]] = []

        for reaction in message.reactions:
            users = []

            async for user in reaction.users():
                users.append(str(user))

            to_add.append((str(reaction), users))
        
        return [ReactionData(reaction=reaction, users=users) for reaction, users in to_add]

    async def treat_attachements(self, message: Message, folder: str) -> List[str]:
        to_add: List[str] = []

        for n, attachement in enumerate(message.attachments):
            file_format = attachement.url.split(".")[-1]
            path = f"{folder}/{message.created_at.strftime('%Y-%m-%d_%H-%M-%S')}_{n}.{file_format}"

            try:
                await attachement.save(path, use_cached=True)
                to_add.append("/".join(path.split("/")[3:])) # keeping file name only

            except (HTTPException, NotFound):
                pass

        return to_add

    ########################################### COMMANDS ##########################################

    @group(name="backup")
    async def backup_group(self, ctx: Context):
        pass

    @backup_group.command(name="start")
    async def backup_start(self, ctx: Context):
        guild = ctx.guild

        for channel in guild.channels:
            if isinstance(channel, TextChannel):
                channel_config = self.config.channel(channel)

                try:
                    os.mkdir(channel_config.file.removesuffix(".json")) # creating folders for files
                except FileExistsError:
                    pass

                channel_config.set(self.defaults) # reset to avoid overlap

        await self.treat_guild(guild, progress_channel=ctx.channel)
