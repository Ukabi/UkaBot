############################################# IMPORTS #############################################

#################### DISCORD ####################
from discord.ext.commands import Context
from discord.ext.commands import (
    check,
    check_any,
    has_permissions
)

############################################ PREDICATES ###########################################

def is_owner_predicate(ctx: Context):
    if ctx.guild is None:
        return False
    else:
        return ctx.guild.owner_id == ctx.author.id

def is_bot_owner_predicate(ctx: Context):
    return ctx.bot.owner_id == ctx.author.id

############################################## CHECKS #############################################

def admin():
    return has_permissions(administrator=True)

def is_owner():
    return check(is_owner_predicate)

def admin_or_permissions(**perms):
    return check_any(
        has_permissions(administrator=True),
        has_permissions(**perms)
    )

def owner_or_permissions(**perms):
    return check_any(
        check(is_owner_predicate),
        has_permissions(**perms)
    )

def is_bot_owner():
    return check(is_bot_owner_predicate)
