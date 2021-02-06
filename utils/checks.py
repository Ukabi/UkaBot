############################################# IMPORTS #############################################

#################### DISCORD ####################
from discord.ext.commands import Context
from discord.ext.commands import (
    check,
    check_any,
    has_permissions
)

##################### UTILS #####################

############################################ FUNCTIONS ############################################

def admin():
    return has_permissions(administrator=True)

def is_owner():
    def predicate(ctx: Context):
        if ctx.guild is None:
            return False
        return ctx.guild.owner_id == ctx.author.id
    return check(predicate)

def admin_or_permissions(**perms):
    return check_any(admin, has_permissions(**perms))

def owner_or_permissions(**perms):
    return check_any(is_owner, has_permissions(**perms))

def is_bot_owner():
    def predicate(ctx: Context):
        return ctx.bot.owner_id == ctx.author.id
    return check(predicate)