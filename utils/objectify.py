############################################# IMPORTS #############################################

from typing import (
    Any,
    Dict,
    Iterable,
    List,
    Union
)

############################################# GLOBALS #############################################

# list of impossible attributes for `Objectify` class defined bellow else creates infinite
# loops since `object.__getattribute__` and `object.__setattr__` are redefined there
FORBIDDEN_KEYS = [
    "__base__", "__bases__", "__class__", "__dict__", "__module__",
    "__weakref__", "_instanceobject", *(dict.__dict__.keys())
]

############################################# CLASSES #############################################

class Objectify(dict):
    """A more intuitive way to manipulate json-like dicts.
    Transforms any json-like `dict` into a both key and
    attribute-oriented class.

    Example: `foo['bar'][0]['key']` <=> `foo.bar[0].key`

    /!\ Parent (`dict`) attributes can't be provided,
    they're either ignored or might break the class.

    """
    def __init__(self, arg: Union[dict, Iterable], **kwargs):
        super().__init__(arg, **kwargs)

        for name, value in super().items():
            self._instanceobject(name, value)

    def __getattribute__(self, name):
        if name in FORBIDDEN_KEYS:
            return super().__getattribute__(name)
        else:
            return self[name]

    def __setattr__(self, name, value):
        if name in FORBIDDEN_KEYS:
            super().__setattr__(name, value)
        else:
            self._instanceobject(name, value)

    def _instanceobject(self, name, value):
        if isinstance(value, (list, tuple)):
            self[name] = [Objectify(x) if isinstance(x, dict) else x for x in value]
        elif isinstance(value, (dict, Objectify)):
            self[name] = Objectify(value)
        else:
            self[name] = value

############################################ FUNCTIONS ############################################

def objectify(iterable: Union[dict, list, tuple]) -> Union[List[Objectify], Objectify]:
    """Main operation: transposes any simple `dict` or
    `list`-like iterable into an `Objectify`-composed object.

    Parameters
        instance: Union[`dict`, `list`, `tuple`]
            The object to operate on

    Returns
        Union[List[`Objectify`], `Objectify`]
            Result of transposition

    """
    if isinstance(iterable, dict):
        return Objectify(iterable)
    elif isinstance(iterable, (list, tuple)):
        return [Objectify(x) if isinstance(x, dict) else x for x in iterable]
    else:
        raise TypeError('Object must be list, tuple or dict')
