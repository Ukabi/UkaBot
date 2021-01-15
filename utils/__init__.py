############################################# IMPORTS #############################################

##################### UTILS #####################
import json

############################################ FUNCTIONS ############################################

def load(path, iferror=list()):
    try:
        with open(path, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        with open(path, 'x') as file:
            file.write(iferror)
        return iferror

def write(path, data):
    with open(path, 'w') as file:
        file.write(json.dumps(data))

############################################# CLASSES #############################################

class Objectify:
    def __init__(self, d: dict):
        for key, val in d.items():
            if isinstance(val, (list, tuple, set, frozenset)):
               setattr(
                   self,
                   key,
                   [Objectify(x) if isinstance(x, dict) else x for x in val]
                )

            else:
               setattr(
                   self,
                   key,
                   Objectify(val) if isinstance(val, dict) else val
                )