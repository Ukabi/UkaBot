############################################# IMPORTS #############################################

#################### DISCORD ####################
from discord import (
    File,
    Member,
    Message,
    Role
)
from discord import HTTPException
from discord.ext.commands import Context
from discord.ext.commands import (
    check,
    check_any,
    has_permissions
)

##################### UTILS #####################
from typing import Tuple

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

############################################ FUNCTIONS ############################################

async def ask_confirmation(
    ctx: Context, file: File = None, message: str = "Type {}/{} to confirm",
    conditions: Tuple[str and str] = ("y", "n")
) -> bool:
    """A general confirmation message request.

    Parameters
        ctx: `Context`
            The command `Context`
        file: `File` = `None`
            The `File` to send (optionnal)
        message: `str` = `"Type {}/{} to confirm"`
            The message that will tell the `User` that a confirmation is required
            Must contain 2 blank fields to fill in condition criteria
        condition: Tuple[`str` and `str`] = `("y", "n")`
            The yes or no pass conditions

    Returns
        `bool`
            `True` if Union[`User`, `Member`] replies with "yes"
            condition (default: y), or `False` if they reply with
            "no" condition (default: n)

    """
    def check(m: Message):
        return all([
            m.channel == ctx.channel,       # channel matching
            m.author == ctx.message.author, # author matching
            m.content.lower().split()[0] in conditions if m.content else False
        ])    # ^ content matching (with special case being empty case ^)

    prompt = await ctx.send(message.format(*conditions), file=file)
    confirm = await ctx.bot.wait_for('message', check=check)
    if confirm.content.lower().startswith(conditions[0]):
        await prompt.delete()
        try:
            await confirm.delete()
        except HTTPException:
            pass
        return True
    else:
        return False

def can_give_role(role: Role, client: Member) -> bool:
    """Determines whether `Member` can give provided `Role` or not.

    Parameters
        role: `Role`
            The `Role` to compare
        client: `Member`
            The `Member` to compare

    Returns
        `bool`
            `True` if client highest role with right is above role,
            else `False`

    """
    def condition(r: Role):
        perms = r.permissions
        return r and (perms.administrator or perms.manage_roles)

    client_roles_with_rights = [r for r in client.roles if condition(r)]
    client_max_rank = max([r.position for r in client_roles_with_rights])

    return role.position < client_max_rank
