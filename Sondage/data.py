############################################# IMPORTS #############################################

from typing import List
from utils.objectify import Objectify

############################################# CLASSES #############################################


class Guild(Objectify):
    channels: List[int]
    log: int

    def __init__(self, channels: List[int], log: int):
        super().__init__(channels=channels, log=log)
