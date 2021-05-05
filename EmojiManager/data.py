############################################# IMPORTS #############################################

from discord import (
    Emoji,
    Role
)
from pathlib import Path
from typing import Union

############################################# GLOBALS #############################################

PATH = f'{Path(__file__).absolute()}/emojis'
EmojiTypes = Union[int, str, Emoji]
RoleTypes = Union[int, str, Role]