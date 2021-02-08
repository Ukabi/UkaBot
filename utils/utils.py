############################################# IMPORTS #############################################

#################### DISCORD ####################
from discord import (
    Embed,
    File
)
from discord.ext.commands import (
    Bot,
    Context
)

##################### UTILS #####################
from typing import (
    Any,
    Dict,
    List,
    Union
)

from .config import Group
from .objectify import Objectify

############################################ FUNCTIONS ############################################

async def ask_confirmation(ctx: Context, bot: Bot, pic: File = None,
                           message: str = "Type y/n to confirm"):
    """A general confirmation message request.

    Parameters
        ctx: `Context`
            The command `Context`
        bot: `Bot`
            The `Bot`
        pic: `File = None`
            The `File` to send
        message: `str = "Type y/n to confirm"`
            The message that will tell the `User` that a confirmation
            is required
    
    Returns
        `bool`
            `True` if `User` replies with `y`,
            or `False` if they reply with `n`

    """
    def check(m):
        return not any(
            m.channel != ctx.channel,
            m.author != ctx.message.author,
            m.content.lower()[:1] not in "yn"
        )

    await ctx.send(message, file=pic)
    confirm = await bot.wait_for('message', check=check)
    return confirm.content.lower().startswith("y")

def update_config(config: Group, attribute: str,
                  value: Union[List[Objectify], Objectify, List[Any], Dict[str, Any]]):
    """A general function for configuration file updating.

    Parameters
        config: `Group`
            The config file to edit
        attribute: `str`
            The attribute to edit
        value: `Union[List[`Objectify`], `Objectify`, List[Any], Dict[str, Any]]`
            The value to set

    """
    config_data = config.get()

    if Objectify.is_objectify(config_data):
        if Objectify.is_objectify(value):
            setattr(config_data, attribute, value)
        else:
            setattr(config_data, attribute, Objectify.objectify(value))
    else:
        if Objectify.is_objectify(value):
            config_data[attribute] = Objectify.dictify(value)
        else:
            config_data[attribute] = value

    config.set(config_data)
