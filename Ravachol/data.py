############################################# IMPORTS #############################################

from discord import Message
from discord.ext.commands import Bot

from utils.objectify import Objectify
from typing import List

import random

############################################# CLASSES #############################################


class Event(Objectify):
    trigger: str
    content: List[str]
    frequency: float

    def __init__(self, trigger: str, content: List[str], frequency: float):
        super().__init__(trigger=trigger, content=content, frequency=frequency)

    def filter(self, message: Message, bot: Bot) -> bool:
        user_id = message.author.id
        bot_id = bot.user.id

        if user_id != bot_id and self.trigger in message.content:
            return self.frequency == 1 or self.frequency - random.random() > 0
        return False

    def get(self):
        if len(self.content) == 1:
            return self.content[0]

        return random.choice(self.content)


class Guild(Objectify):
    events: List[Event]

    def __init__(self, events: List[Event]):
        super().__init__(events=events)
