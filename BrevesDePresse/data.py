############################################# IMPORTS #############################################

from typing import List
from utils.objectify import Objectify

############################################# CLASSES #############################################


class Guild(Objectify):
    channels: List[int]

    def __init__(self, channels: int):
        super().__init__(channels=channels)
