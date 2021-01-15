############################################# IMPORTS #############################################

#################### DISCORD ####################
from discord.ext.commands import (
    Bot,
    Context
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
    'birthday': Birthday,
    'cleanup': CleanUp,
    'emojidata': EmojiData,
    'emojimanager': EmojiManager,
    'poll': Poll,
    'rolebyreaction': RoleByReaction,
    'scheduler': Scheduler,
    'welcome': Welcome
}
PREFIX = '!'
TOKEN = 'NTczMTI4NTI1NzU0OTI1MDY2.XMmViA.CPKxKNW2gT7py5WoYmSosGCI7ic'

bot = Bot(command_prefix=PREFIX)

############################################ FUNCTIONS ############################################

def load_cogs(client: Bot, cogs: list):
    [client.add_cog(cog) for cog in [cog(client) for cog in cogs]]

def unload_cogs(client: Bot, cogs: list):
    [client.remove_cog(cog) for cog in cogs]

def get_cogs(client: Bot):
    return {name.lower(): cog for name, cog in client.cogs.items()}

def get_cog_names(client: Bot):
    return sorted([name.lower() for name in client.cogs.keys()])

############################################# EVENTS ##############################################

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    print(f'{get_cogs(bot)}')

############################################ COMMANDS #############################################

@bot.group(name='cog')
async def cog_group(ctx: Context):
    pass

@cog_group.command(name='load')
async def cog_load(ctx: Context, *, cog_names: str):
    try:
        cog_names = cog_names.split()
        cogs = list()
        for cog_name in cog_names:
            cogs.append(COGS[cog_name])
        load_cogs(bot, cogs)
        print(f'{get_cogs(bot)}')

    except KeyError:
        await ctx.send(f'Error: {cog_name} not found.')

@cog_group.command(name='unload')
async def cog_unload(ctx: Context, *, cog_names: str):
    try:
        cog_names = cog_names.split()
        loaded_cogs = get_cogs(bot)
        cogs = list()
        for cog_name in cog_names:
            cogs.append(loaded_cogs[cog_name])
        unload_cogs(bot, cogs)
        print(f'{get_cogs(bot)}')

    except KeyError:
        await ctx.send(f'Error: {cog_name} not loaded.')

@cog_group.command(name='list')
async def cog_list(ctx: Context):
    await ctx.send(", ".join(get_cog_names(bot)))

############################################## MAIN ###############################################

if __name__ == '__main__':
    bot.run(TOKEN)