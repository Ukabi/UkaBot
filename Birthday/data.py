############################################ IMPORTS ##############################################

from utils.objectify import Objectify

############################################ CLASSES ##############################################

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
