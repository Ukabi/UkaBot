############################################# IMPORTS #############################################

from utils.objectify import Objectify
from typing import (
    List,
    Tuple,
    Union
)
import time

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

    def __bool__(self) -> bool:
        return bool(self.day and self.month)

    def __str__(self) -> str:
        return f"{self.day} {Date.convert_month(self.month)}"

    @staticmethod
    def convert_date(day: Union[int, str], month: Union[int, str]) -> "Date":
        date = time.strptime(f"{day} {month}", "%d %m")
        return Date(day=date.tm_mday, month=date.tm_mon)

    @staticmethod
    def convert_month(month: int) -> str:
        return MONTHS[month - 1]

class Member(Objectify):
    birthday: Date
    name: str

    def __init__(self, birthday: Date, name: str):
        super().__init__(birthday=birthday, name=name)

    def __str__(self) -> str:
        return f"{self.name} - {self.birthday}"
