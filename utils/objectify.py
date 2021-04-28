############################################# IMPORTS #############################################

from typing import (
    Any,
    Dict,
    Iterable,
    List,
    Union
)

############################################# GLOBALS #############################################

FORBIDDEN_KEYS = [                                          # list of impossible attributes for
    "__base__", "__bases__", "__class__", "__dict__",       # `Objectify` class defined bellow
    "__module__", "__weakref__", *(dict.__dict__.keys())    # else creates infinite loops since
]                                                           # `dict.__getattribute__` is redefined

############################################# CLASSES #############################################

class Objectify(dict):
    """A more intuitive way to manipulate json-like dicts.
    Transforms any json-like `dict` into a both key and
    attribute-oriented class.

    Example: `foo['bar'][0]['key']` <-> `foo.bar[0].key`

    """
    def __init__(self, iterable: dict, **kwargs):
        super().__init__(iterable, **kwargs)

        for key, val in super().items():
            if isinstance(val, (list, tuple)):
                self[key] = [Objectify(x) if isinstance(x, dict) else x for x in val]
            elif isinstance(val, (dict, Objectify)):
                self[key] = Objectify(val)
            else:
                self[key] = val

    def __getattribute__(self, name):
        if name in FORBIDDEN_KEYS:
            return super().__getattribute__(name)
        else:
            return self[name]

############################################ FUNCTIONS ############################################

def is_objectify(instance: Any) -> bool:
    """Verifies if the instance contains any `Objectify` component.

    Parameters
        instance: Any
            The object to operate on

    Returns
        `bool`
            `True` if any `Objectify` object in the tree else `False`

    """
    if isinstance(instance, (list, tuple)):
        return any(isinstance(x, Objectify) for x in instance)
    else:
        return isinstance(instance, Objectify)

def objectify(iterable: Union[dict, list, tuple]) -> Union[List[Objectify], Objectify]:
    """Main operation: transposes any simple `dict` or `list` into an
    attribute-oriented object.

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
        return [Objectify(x) for x in iterable]
    else:
        raise TypeError('Object must be list, tuple or dict')