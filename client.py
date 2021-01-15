############################################# IMPORTS #############################################

#################### DISCORD ####################
from discord.ext.commands import (
    Bot,
    Context,
    Group
)

##################### COGS ######################
from Birthday import Birthday
from CleanUp import CleanUp
from EmojiData import EmojiData
from EmojiManager import EmojiManager
from Poll import Poll
from RoleByReaction import RoleByReaction
from Scheduler import Scheduler
from Welcome import Welcome

############################################# GLOBAL ##############################################

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
PREFIX = '!'
TOKEN = 'NTczMTI4NTI1NzU0OTI1MDY2.XMmViA.CPKxKNW2gT7py5WoYmSosGCI7ic'

bot = Bot(command_prefix=PREFIX)

############################################ FUNCTIONS ############################################

def load_cogs(client: Bot, cogs: list):
    [client.add_cog(cog) for cog in [cog(client) for cog in cogs]]

def unload_cogs(client: Bot, cogs: list):
    [client.remove_cog(cog) for cog in cogs]

def get_commands(instance: 'Union[Bot, Group]'):
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
    cog_names = {name.lower() for name in bot.cogs.keys()}

    print(f'Bot prefix: {PREFIX}')
    print(f'Logged in as {bot.user}')
    print(f'Loaded cogs: {", ".join(cog_names)}')
    print(
        f'{len(cog_names)} cogs and '
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