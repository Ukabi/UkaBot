############################################# IMPORTS #############################################

#################### DISCORD ####################
from discord import Intents
from discord.ext.commands import (
    Bot,
    Cog,
    Context,
    Group
)
from discord.ext.commands import command

##################### COGS ######################
from Birthday import Birthday
#from CleanUp import CleanUp
#from EmojiData import EmojiData
#from EmojiManager import EmojiManager
from Poll import Poll
from RoleByReaction import RoleByReaction
from Event import Event
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
from utils.exceptions import InvalidArguments

############################################# GLOBAL ##############################################

COG_PATH = 'cogs.json'
COGS = {
    Birthday,
#    CleanUp,
#    EmojiData,
#    EmojiManager,
    Poll,
    RoleByReaction,
    Event,
    Welcome
}
NAMES_COGS_MAP = {cog.__name__.lower(): cog for cog in COGS}

CONFIG_PATH = 'config.json'
BOT_CONFIG = load(CONFIG_PATH, if_error={})

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

intents = Intents.all()
bot = Bot(
    command_prefix=PREFIX,
    intents=intents
)

############################################ FUNCTIONS ############################################

def load_cogs(client: Bot, cogs: List[Cog]):
    """Loads cogs on client.

    Parameters
        client: `Bot`
            The client to load the cogs on
        cogs: `List[Cog]`
            The `list` of `Cog` to load

    """
    for cog in cogs:
        cog = cog(client)
        client.add_cog(cog)

def unload_cogs(client: Bot, cogs: List[Cog]):
    """Unloads cogs from client.

    Parameters
        client: `Bot`
            The client to load the cogs on
        cogs: `List[Cog]`
            The `list` of `Cog` to unload

    """
    for cog in cogs:
        client.remove_cog(cog.__name__)

def get_commands(instance: Union[Bot, Group]) -> List[command]:
    """Gets loaded commands from client.

    Parameters
        instance: `Union[Bot, Group]`
            The instance to look for commands in
    
    Returns
        `List[command]`
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
    cog_names_to_load = load(COG_PATH, if_error=[])
    cogs_to_load = {NAMES_COGS_MAP[cog_name] for cog_name in cog_names_to_load}
    load_cogs(bot, cogs_to_load)

    loaded_cogs_names = sorted({name.lower() for name in bot.cogs.keys()})

    print(f'Bot prefix: {PREFIX}')
    print(f'Logged in as {bot.user}')
    print(f'Loaded cogs: {", ".join(loaded_cogs_names)}')
    print(
        f'{len(loaded_cogs_names)} cogs, '
        f'{len(get_commands(bot))} commands'
    )

############################################ COMMANDS #############################################

@bot.group(name='cog')
async def cog_group(ctx: Context):
    pass

@cog_group.command(name='load')
async def cog_load(ctx: Context, *, cog_names: str):
    loaded_cog_names = {name.lower() for name in bot.cogs.keys()}

    cog_names = cog_names.lower().split()

    try:
        to_load = set()
        for cog_name in cog_names:
            if cog_name not in loaded_cog_names:
                to_load.add(NAMES_COGS_MAP[cog_name])
            else:
                raise ValueError
    except KeyError:
        error = InvalidArguments(
            ctx=ctx,
            message=f"{cog_name} not found"
        )
        await error.execute()
    except ValueError:
        error = InvalidArguments(
            ctx=ctx,
            message=f"{cog_name} already loaded"
        )
        await error.execute()

    else:
        load_cogs(bot, to_load)
        write(COG_PATH, [name.lower() for name in bot.cogs.keys()])

        await ctx.send(f'Successfully loaded {", ".join(cog_names)}')

@cog_group.command(name='unload')
async def cog_unload(ctx: Context, *, cog_names: str):
    loaded_cog_names = {name.lower() for name in bot.cogs.keys()}

    cog_names = cog_names.lower().split()

    try:
        to_unload = set()
        for cog_name in cog_names:
            if cog_name in loaded_cog_names:
                to_unload.add(NAMES_COGS_MAP[cog_name])
            elif cog_name not in NAMES_COGS_MAP.keys():
                raise KeyError
            else:
                raise ValueError
    except KeyError:
        error = InvalidArguments(
            ctx=ctx,
            message=f"{cog_name} not found"
        )
        await error.execute()
    except ValueError:
        error = InvalidArguments(
            ctx=ctx,
            message=f"{cog_name} not loaded"
        )
        await error.execute()

    else:
        unload_cogs(bot, to_unload)

        loaded_cog_names = {name.lower() for name in bot.cogs.keys()}
        write(COG_PATH, [cog_name for cog_name in loaded_cog_names if cog_name not in cog_names])

        await ctx.send(f'Successfully unloaded {", ".join(cog_names)}')

@cog_group.command(name='list')
async def cog_list(ctx: Context):
    cog_names = sorted({name.lower() for name in bot.cogs.keys()})
    message = ", ".join(cog_names) if cog_names else "No cog loaded"

    await ctx.send(message)

@bot.command(name='commands')
async def bot_commands(ctx: Context):
    command_names = [f"{c.full_parent_name} {c.name}" for c in get_commands(bot)]
    message = ", ".join(command_names) if command_names else "No command loaded"

    await ctx.send(message)

############################################## MAIN ###############################################

if __name__ == '__main__':
    bot.run(TOKEN)
