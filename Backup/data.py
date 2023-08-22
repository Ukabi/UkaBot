############################################# IMPORTS #############################################

from datetime import datetime as dt
from utils.objectify import Objectify
from typing import List

############################################# CLASSES #############################################

class Reaction(Objectify):
    reaction: str
    users: List[str]

    def __init__(self, reaction: str, users: List[str]):
        super().__init__(reaction=reaction, users=users)
    
    def __str__(self) -> str:
        return f'Reaction {self.reaction} by {", ".join(self.users)}'

class Message(Objectify):
    date: float
    channel: str
    member: str
    text: str
    reactions: List[Reaction]
    attachments: List[str]

    def __init__(
        self, date: float, channel: str, member: str, text: str,
        reactions: List[Reaction], attachments: List[str]
    ):
        super().__init__(
            date=date, channel=channel, member=member, text=text,
            reactions=reactions, attachments=attachments
        )
    
    def __str__(self) -> str:
        ret = f'[{dt.fromtimestamp(self.date).strftime("%d %b %Y - %H:%M")}] {self.member} : {self.text}'
        if self.attachments:
            ret += "\n " + "\n".join([f'Attachment {a}' for a in self.attachments])
        if self.reactions:
            ret += "\n" + "\n".join([str(r) for r in self.reactions])
        
        return ret

class Channel(Objectify):
    data: List[Message]

    def __init__(self, data: List[Message]):
        super().__init__(data=data)

    def __str__(self) -> str:
        return "\n\n".join([str(message) for message in sorted(self.data, key=lambda m: m.date)])
