############################################# IMPORTS #############################################

from utils.objectify import Objectify

############################################# GLOBALS #############################################

FIGURES = {n: f'{n}\u20e3' for n in range(1, 10)}
SEP = '|'

############################################# CLASSES #############################################

class Guild(Objectify):
    channel: int

    def __init__(self, channel: int):
        super().__init__(channel=channel)
