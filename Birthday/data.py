############################################# IMPORTS #############################################

from utils.objectify import Objectify

############################################# GLOBALS #############################################

MONTHS = [
    "Jan", "Feb", "Mar", "Apr",
    "May", "Jun", "Jul", "Aug",
    "Sep", "Oct", "Nov", "Dec"
]

############################################# CLASSES #############################################

class Guild(Objectify):
    channel: int
    role: int

    def __init__(self, channel: int, role: int):
        super().__init__(channel=channel, role=role)

class Date(Objectify):
    day: int
    month: int

    def __init__(self, day: int, month: int):
        super().__init__(day=day, month=month)

class Member(Objectify):
    birthday: Date
    name: str

    def __init__(self, birthday: Date, name: str):
        super().__init__(birthday=birthday, name=name)
