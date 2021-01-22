############################################# IMPORTS #############################################

from utils.Objectify import Objectify
from utils.utils import (
    load,
    write
)

############################################# CLASSES #############################################

class Group:
    def __init__(self, file: str, defaults: Union[list, dict] = {}):
        self.file = file
        self.data = load(
            self.file,
            if_error=defaults,
            to_object=True
        )

    def get(self):
        return self.data

    def set(self, data: Objectify):
        write(self.file, data)
        self.data = data