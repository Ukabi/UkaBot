############################################# IMPORTS #############################################

from datetime import datetime as dt
from datetime import timedelta as td
from utils.objectify import Objectify
from typing import List

############################################# GLOBALS #############################################

MONTHS = [
    "Jan", "Feb", "Mar", "Apr",
    "May", "Jun", "Jul", "Aug",
    "Sep", "Oct", "Nov", "Dec"
]
DATETIME_FORMAT = "%Y-%m-%d_%H:%M:%S"

############################################# CLASSES #############################################

class Event(Objectify):
    channel: int
    date: float
    participants: List[int]
    title: str

    def __init__(self, channel: int, date: float, participants: List[int], title: str):
        super().__init__(channel=channel, date=date, participants=participants, title=title)

    def __eq__(self, event: "Event") -> bool:
        return event.date == self.date and event.title == self.title

    def __str__(self) -> str:
        return f"{self.date} - {self.title}"

    @staticmethod
    def timestamp(date: str) -> float:
        return dt.strptime(date, DATETIME_FORMAT).timestamp()

    def datetime(self) -> dt:
        return dt.fromtimestamp(self.date)

    def elapsed(self) -> bool:
        return self.how_far() < 0

    def how_far(self) -> float:
        return (self.datetime() - dt.now()).total_seconds()

class Guild(Objectify):
    events: List[Event]

    def __init__(self, events: List[Event]):
        super().__init__(events=events)
