############################################# IMPORTS #############################################

from typing import (
    Any,
    Dict,
    List,
    Union
)

############################################# CLASSES #############################################

class Objectify:
    """A more intuitive way to manipulate json-like dicts.
    Transforms any json-like `dict` into an attribute-oriented class.

    Example: `foo['bar'][0]['key']` <-> `foo.bar[0].key`

    """
    def __init__(self, instance: Union[dict, "Objectify"]):
        if isinstance(instance, dict):
            d = instance
        elif isinstance(instance, Objectify):
            d = instance.__dict__
        else:
            raise TypeError

        for key, val in d.items():
            if isinstance(val, (list, tuple)):
                setattr(
                    self,
                    key,
                    [Objectify(x) if isinstance(x, (dict, Objectify)) else x for x in val]
                    )
            elif isinstance(val, (dict, Objectify)):
                setattr(self, key, Objectify(val))
            else:
                setattr(self, key, val)

        # Just for the fun
        # [setattr(self, key, [Objectify(x) if isinstance(x, (dict, Objectify)) else x for x in val]) if isinstance(val, (list, tuple)) else setattr(self, key, Objectify(val)) if isinstance(val, (dict, Objectify)) else setattr(self, key, val) for key, val in d.items()]

    def __repr__(self):
        return str(dictify(self))

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
        return any([is_objectify(x) for x in instance])
    elif isinstance(instance, dict):
        return any([is_objectify(x) for x in instance.values()])
    else:
        return isinstance(instance, Objectify)

    # Just for the fun
    # return any([is_objectify(x) for x in instance]) if isinstance(instance, (list, tuple)) else any([is_objectify(x) for x in instance.values()]) if isinstance(instance, dict) else isinstance(instance, Objectify)

def objectify(instance: Union[dict, list, tuple]) -> Union[List[Objectify], Objectify]:
    """Main operation: transposes any simple `dict` or `list` into an
    attribute-oriented object.

    Parameters
        instance: Union[`dict`, `list`, `tuple`]
            The object to operate on

    Returns
        Union[List[`Objectify`], `Objectify`]
            Result of transposition

    """
    if isinstance(instance, dict):
        return Objectify(instance)
    elif isinstance(instance, (list, tuple)):
        return [Objectify(x) for x in instance]
    else:
        raise TypeError('Object must be list, tuple or dict')

def dictify(instance: Union[List[Objectify], Objectify, list, dict]) -> Union[list, dict]:
    """Inverted operation: transposes any `Objectify`-composed object into a `dict`.

    Parameters
        instance: Union[List[`Objectify`], `Objectify`, `list`, `dict`]
            The object to operate on

    Returns
        Union[`list`, `dict`]
            Result of transposition

    """
    if isinstance(instance, (list, tuple)):
        return [dictify(x) for x in instance]
    elif isinstance(instance, dict):
        return {key: dictify(val) for key, val in instance.items()}
    elif not isinstance(instance, Objectify):
        return instance
    else:
        d = dict()
        for key, val in instance.__dict__.items():
            if isinstance(val, list):
                d[key] = [dictify(x) if isinstance(x, Objectify) else x for x in val]
            else:
                d[key] = dictify(val) if isinstance(val, Objectify) else val
        return d

    # Just for the fun
    # return [dictify(x) for x in instance] if isinstance(instance, (list, tuple)) else {key: dictify(val) for key, val in instance.items()} if isinstance(instance, dict) else instance if not isinstance(instance, Objectify) else {k: [dictify(x) if isinstance(x, Objectify) else x for x in v] if isinstance(v, list) else dictify(v) if isinstance(v, Objectify) else v for k, v in instance.__dict__.items()}
