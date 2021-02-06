############################################# IMPORTS #############################################

#################### DISCORD ####################
from discord.ext.commands import (
    Bot,
    Cog,
    Context,
    Group
)
from discord.ext.commands import command

##################### COGS ######################
from Birthday import Birthday
from CleanUp import CleanUp
from EmojiData import EmojiData
from EmojiManager import EmojiManager
from Poll import Poll
from RoleByReaction import RoleByReaction
from Scheduler import Scheduler
from Welcome import Welcome

##################### UTILS #####################
from typing import (
    List,
    Union
)
from utils import (
    load,
    write
)

############################################# GLOBAL ##############################################

COG_PATH = 'cogs.json'
COGS = {
    Birthday,
    CleanUp,
    EmojiData,
    EmojiManager,
    Poll,
    RoleByReaction,
    Scheduler,
    Welcome
}

CONFIG_PATH = 'config.json'
BOT_CONFIG = load(CONFIG_PATH, {})

PREFIX = BOT_CONFIG.get('prefix', None)
while not PREFIX:
    PREFIX = input('Choose bot prefix: ')
    if PREFIX:
        BOT_CONFIG['prefix'] = PREFIX
        write(CONFIG_PATH, BOT_CONFIG)

TOKEN = BOT_CONFIG.get('token', None)
while not TOKEN:
    TOKEN = input('Enter bot token: ')
    if TOKEN:
        BOT_CONFIG['token'] = TOKEN
        write(CONFIG_PATH, BOT_CONFIG)

bot = Bot(command_prefix=PREFIX)

############################################ FUNCTIONS ############################################

def load_cogs(client: Bot, cogs: List[Cog]):
    """Loads cogs on client.

    Parameters
        client: Bot
            The client to load the cogs on
        cogs: List[Cog]
            The `list` of `Cog` to load

    """
    [client.add_cog(cog) for cog in [cog(client) for cog in cogs]]

def unload_cogs(client: Bot, cogs: List[str]):
    """Unloads cogs from client.

    Parameters
        client: Bot
            The client to load the cogs on
        cogs: List[Cog]
            The `list` of `str` to unload, strings being the `Cog` class name

    """
    [client.remove_cog(cog) for cog in cogs]

def get_commands(instance: Union[Bot, Group]) -> List[command]:
    """Gets loaded commands from client.

    Parameters
        instance: Union[Bot, Group]
            The instance to look for commands in
    
    Returns
        List[command]
            The `list` of `command` loaded on client

    """
    commands = list()
    for command in instance.commands:
        if isinstance(command, Group):
            commands += get_commands(command)
        else:
            commands.append(command)
    return commands

############################################# EVENTS ##############################################

@bot.event
async def on_ready():
    """This runs when bot has done logging in and setting up.

    """
    names_cogs_map = {cog.__name__.lower(): cog for cog in COGS}
    cog_names_to_load = load(COG_PATH)
    cogs_to_load = [names_cogs_map[cog_name] for cog_name in cog_names_to_load]
    load_cogs(bot, cogs_to_load)

    loaded_cogs_names = {name.lower() for name in bot.cogs.keys()}

    print(f'Bot prefix: {PREFIX}')
    print(f'Logged in as {bot.user}')
    print(f'Loaded cogs: {", ".join(loaded_cogs_names)}')
    print(
        f'{len(loaded_cogs_names)} cogs and '
        f'{len(get_commands(bot))} commands loaded'
    )

############################################ COMMANDS #############################################

@bot.group(name='cog')
async def cog_group(ctx: Context):
    pass

@cog_group.command(name='load')
async def cog_load(ctx: Context, *, cog_names: str):
    async with ctx.typing():
        try:
            names_cogs_map = {cog.__name__.lower(): cog for cog in COGS}
            loaded_cog_names = [name.lower() for name in bot.cogs.keys()]

            cog_names = cog_names.lower().split()

            to_load = list()
            for cog_name in cog_names:
                if cog_name not in loaded_cog_names:
                    to_load.append(names_cogs_map[cog_name])
                else:
                    await ctx.send(f'Error: {cog_name} already loaded.')
                    return

            load_cogs(bot, to_load)
            write(COG_PATH, load(COG_PATH) + cog_names)
            await ctx.send(f'Successfully loaded {", ".join(cog_names)}')

        except KeyError:
            await ctx.send(f'Error: {cog_name} not found.')

@cog_group.command(name='unload')
async def cog_unload(ctx: Context, *, cog_names: str):
    async with ctx.typing():
        try:
            names_cogs_map = {cog.__name__.lower(): cog.__name__ for cog in COGS}
            loaded_cog_names = [name.lower() for name in bot.cogs.keys()]

            cog_names = cog_names.lower().split()

            to_unload = list()
            for cog_name in cog_names:
                if cog_name in loaded_cog_names:
                    to_unload.append(names_cogs_map[cog_name])
                elif cog_name not in names_cogs_map.keys():
                    raise KeyError
                else:
                    await ctx.send(f'Error: {cog_name} not loaded.')
                    return

            unload_cogs(bot, to_unload)
            write(COG_PATH, [cog_name for cog_name in load(COG_PATH) if cog_name not in cog_names])
            await ctx.send(f'Successfully unloaded {", ".join(cog_names)}')

        except KeyError:
            await ctx.send(f'Error: {cog_name} not found.')

@cog_group.command(name='list')
async def cog_list(ctx: Context):
    async with ctx.typing():
        cog_names = {name.lower() for name in bot.cogs.keys()}
        await ctx.send(", ".join(cog_names))

@bot.command(name='commands')
async def bot_commands(ctx: Context):
    async with ctx.typing():
        command_names = [c.name for c in get_commands(bot)]
        await ctx.send(", ".join(command_names))

############################################## MAIN ###############################################

if __name__ == '__main__':
    bot.run(TOKEN)