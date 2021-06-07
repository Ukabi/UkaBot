############################################# IMPORTS #############################################

from discord import (
    Emoji,
    TextChannel
)

from typing import (
    List,
    Union
)
from utils.objectify import Objectify

############################################# CLASSES #############################################

class Combination(Objectify):
    channel: int
    emoji: Union[int, str]
    message: str

    def __init__(self, channel: int, emoji: int, message: str):
        super().__init__(channel=channel, emoji=emoji, message=message)

class Guild(Objectify):
    channel: int
    combinations: List[Combination]
    message: str
    title: str

    def __init__(self, channel: int, combinations: List[Combination], message: str, title: str):
        super().__init__(channel=channel, combinations=combinations, message=message, title=title)
