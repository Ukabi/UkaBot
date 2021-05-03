############################################# IMPORTS #############################################

from utils.objectify import Objectify

############################################# CLASSES #############################################

class Guild(Objectify):
    channel: int
    message: str
    title: str

    def __init__(self, channel: int, message: str, title: str):
        super().__init__(channel=channel, message=message, title=title)
