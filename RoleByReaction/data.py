############################################# IMPORTS #############################################

from discord import (
    Emoji,
    Role
)

from typing import (
    List,
    Union
)
from utils.objectify import Objectify

############################################# CLASSES #############################################

class Combination(Objectify):
    emoji: Union[int, str]
    role: int

    def __init__(self, emoji: int, role: int):
        super().__init__(emoji=emoji, role=role)

class Guild(Objectify):
    channel: int
    combinations: List[Combination]
    message: str
    title: str

    def __init__(self, channel: int, combinations: List[Combination], message: str, title: str):
        super().__init__(channel=channel, combinations=combinations, message=message, title=title)
