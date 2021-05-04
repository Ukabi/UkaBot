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
        day = f"0{day}" if day < 10 else str(day)
        month = f"0{month}" if month < 10 else str(month)

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

    def sorting_format(self) -> Tuple[str and int and int]:
        return (self.name, self.birthday.day, self.birthday.month)

    @staticmethod
    def from_order(members: List[Tuple[str and int and int]], order: List[int]) -> List["Member"]:
        members = [members[i] for i in order]
        return [Member(
            birthday=Date(
                day=member[1],
                month=member[2]
            ),
            name=member[0]
        ) for member in members]
