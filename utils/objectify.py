############################################# IMPORTS #############################################

from typing import (
    Any,
    Dict,
    List,
    Union
)

############################################# CLASSES #############################################

class Objectify:
    """A more intuitive way to manipulate simple dictionnaries.
    Transforms any json-like `dict` into an attribute-oriented class.

    Example: `foo['bar'][0]['key'] <-> foo.bar[0].key`

    """
    def __init__(self, d: Dict[Any, Any]):
        for key, val in str_key_dict(d).items():
            if isinstance(val, (list, tuple)):
               setattr(
                   self,
                   key,
                   [Objectify(x) if isinstance(x, dict) else x for x in val]
                )
            elif isinstance(val, dict):
               setattr(
                   self,
                   key,
                   Objectify(val) if isinstance(val, dict) else val
                )
            elif isinstance(val, Objectify):
                setattr(
                    self,
                    key,
                    val
                )
            else:
                raise TypeError

    def __repr__(self):
        return str(Objectify.dictify(self))

    @staticmethod
    def objectify(
        instance: Union[dict, list, tuple]
    ) -> Union[List["Objectify"], "Objectify"]:
        """Main operation: transposes any simple `dict` or `list` into an
        attribute-oriented object.

        Parameters
            instance: `Union[dict, list, tuple, set, frozenset]`
                The object to operate on

        Returns
            `Union[List[Objectify], Objectify]`
                Result of transposition

        """
        if isinstance(instance, dict):
            return Objectify(instance)
        elif isinstance(instance, (list, tuple)):
            return [Objectify(x) for x in instance]
        else:
            raise TypeError('Object must be list, tuple or dict')

    @staticmethod
    def dictify(
        instance: Union[List["Objectify"], "Objectify", Any]
    ) -> Union[list, dict]:
        """Inverted operation: transposes any `Objectify`-composed object into a `dict`.

        Parameters
            instance: `Union[List[Objectify], Objectify, Any]`
                The object to operate on

        Returns
            `Union[list, dict]`
                Result of transposition

        """
        if isinstance(instance, (list, tuple)):
            return [Objectify.dictify(x) for x in instance]
        elif isinstance(instance, dict):
            return {key: Objectify.dictify(val) for key, val in instance.items()}
        elif not isinstance(instance, Objectify):
            return instance
        else:
            d = dict()
            for key, val in instance.__dict__.items():
                if isinstance(val, list):
                    d[key] = [Objectify.dictify(x) if isinstance(x, Objectify) else x for x in val]
                else:
                    d[key] = Objectify.dictify(val) if isinstance(val, Objectify) else val
            return d

        # Just for the fun
        # return [Objectify.dictify(x) for x in instance] if isinstance(instance, (list, tuple, set, frozenset)) else {key: Objectify.dictify(val) for key, val in instance.items()} if isinstance(instance, dict) else instance if not isinstance(instance, Objectify) else {k: [Objectify.dictify(x) if isinstance(x, Objectify) else x for x in v] if isinstance(v, list) else Objectify.dictify(v) if isinstance(v, Objectify) else v for k, v in instance.__dict__.items()}

    @staticmethod
    def is_objectify(
        instance: Union[List["Objectify"], "Objectify", Any]
    ) -> bool:
        """Verifies if the instance contains any `Objectify` component.

        Parameters
            instance: `Union[List[Objectify], Objectify, Any]`
                The object to operate on

        Returns
            `bool`
                `True` if any `Objectify` object in the tree else `False`

        """
        if isinstance(instance, (list, tuple)):
            return any([Objectify.is_objectify(x) for x in instance])
        elif isinstance(instance, dict):
            return any([Objectify.is_objectify(x) for x in instance.values()])
        else:
            return isinstance(instance, Objectify)

############################################ FUNCTIONS ############################################

def str_key_dict(value: Dict[Any, Any]) -> Dict[str, Any]:
    """
    Recursively casts all keys in the given `dict` to `str`.

    Parameters
        value: `Dict[Any, Any]`
            The `dict` to cast keys to `str`.

    Returns
        `Dict[str, Any]`
            The `dict` with keys (and nested keys) casted to `str`.

    """
    ret = {}
    for key, val in value.items():
        if isinstance(val, dict):
            val = str_key_dict(val)
        ret[str(key)] = val
    return ret
