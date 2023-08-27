############################################# IMPORTS #############################################

from utils.objectify import Objectify

############################################# CLASSES #############################################


class Guild(Objectify):
    channel: int

    def __init__(self, channel: int):
        super().__init__(channel=channel)
