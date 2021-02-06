############################################# IMPORTS #############################################

#################### DISCORD ####################
from discord.ext.commands import Context

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

def update_config(config: Group, attribute: str, value: Union[List[Objectify], Objectify, List[Any], Dict[str, Any]]):
    """General function for config file updating.

    Parameters
        config: `utils.Group`
            The config file to edit
        attribute: str
            The attribute to edit
        value: Union[List[`Objectify`], `Objectify`, List[Any], Dict[str, Any]]
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