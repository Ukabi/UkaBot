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
    Iterable,
    List,
    Union
)

from .config import Group
from .objectify import Objectify

############################################# CLASSES #############################################

class ImprovedList(list):
    """Some useful functions to explore or transform list content
    more easily.

    """

    def index(
        self, v: Any, start: int = 0, stop: int = 9223372036854775807,
        key: callable = None
    ) -> int:
        """Just like `list.index`, but admits a customizable key for
        easier searches.

        """
        if not key:
            def key(x):
                return x

        for i in range(start, min(len(self), stop)):
            if key(self[i]) == v:
                return i

        raise ValueError("Value not found")

    def get_item(
        self, v: Any, start: int = 0, stop: int = 9223372036854775807,
        key: callable = None
    ):
        """Just like `list.__getitem__`, but admits a customizable key
        for easier searches.

        """
        return self[self.index(v=v, start=start, stop=stop, key=key)]

    @staticmethod
    def flatten(l: Union[list, tuple]):
        """Flattening generic method for various usages.

        """
        while any([isinstance(x, (list, tuple)) for x in l]):
            temp = []
            for x in l:
                temp += x if isinstance(x, (list, tuple)) else [x]
            l = temp
        return l

############################################ FUNCTIONS ############################################

async def ask_confirmation(
    ctx: Context, bot: Bot, file: File = None,
    message: str = "Type y/n to confirm"
):
    """A general confirmation message request.

    Parameters
        ctx: `Context`
            The command `Context`
        bot: `Bot`
            The `Bot`
        file: `File = None`
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
        return not any([                               # and(conditions) <=> not or(not conditions)
            m.channel != ctx.channel,                                            # channel matching
            m.author != ctx.message.author,                                       # author matching
            m.content.lower()[0] not in "yn" if m.content else True              # content matching
        ])                                                   # (with special case being empty case)

    await ctx.send(message, file=file)
    confirm = await bot.wait_for('message', check=check)
    return confirm.content.lower().startswith("y")

def update_config(
    config: Group, attribute: str,
    value: Union[List[Objectify], Objectify, List[Any], Dict[Any, Any]]
):
    """A general function for configuration file updating.

    Parameters
        config: `Group`
            The config file to edit
        attribute: `str`
            The attribute to edit
        value: `Union[List[Objectify], Objectify, List[Any], Dict[Any, Any]]`
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

def get(
    criterion: Any, iterable: Iterable[Any], attribute_condition: str
) -> Any:
    """A general function that returns matching element from an
    `Iterable` considering a certain attribute name and a criterion.

    Parameters
        criterion: `Any`
            The matching condition
        iterable: `Iterable[Any]`
            The `Iterable` to explore
        attribute_condition: str
            The class attribute name to look for
    
    Returns
        `Any`
            The element from iterable that matches with criterion.
            If nothing is found, returns `None`

    """
    for element in iterable:
        if getattr(element, attribute_condition) == criterion:
            return element
