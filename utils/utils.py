############################################# IMPORTS #############################################

from typing import (
    _GenericAlias,
    Any,
    Callable,
    Dict,
    List,
    Union
)

############################################# CLASSES #############################################

class ImprovedList(list):
    """Some useful functions to explore or transform list content
    more easily.

    """

    def index(
        self, v: Any, start: int = 0, stop: int = 9223372036854775807,
        key: Callable = lambda x: x
    ) -> int:
        """Just like `list.index`, but admits a customizable key for
        easier searches.

        """
        for i in range(start, min(len(self), stop)):
            if key(self[i]) == v:
                return i

        raise ValueError("Value not found")

    def get_item(
        self, v: Any, start: int = 0, stop: int = 9223372036854775807,
        key: Callable = lambda x: x
    ) -> Any:
        """Just like `list.__getitem__`, but admits a customizable key
        for easier searches.

        """
        return self[self.index(v=v, start=start, stop=stop, key=key)]

############################################ FUNCTIONS ############################################

def _str_key_json(value: Union[List[Any], Dict[Any, Any]]) -> Union[List[Any], Dict[str, Any]]:
    """Recursively casts all keys in the given json-like Union[List, Dict] to `str`.

    Parameters
        value: Union[List[Any], Dict[Any, Any]]
            The json-like object to cast keys to `str`.

    Returns
        Union[List[Any], Dict[`str`, Any]]
            The json-like object with keys (and nested keys) casted to `str`.

    """
    if isinstance(value, dict):
        ret = {}
        for key, val in value.items():
            if isinstance(val, dict):
                val = _str_key_json(val)
            elif isinstance(val, (list, tuple)):
                val = [_str_key_json(v) for v in val]
            ret[str(key)] = val
        return ret
    elif isinstance(value, (list, tuple)):
        return [_str_key_json(val) for val in value]
    else:
        raise TypeError

def flatten(l: Union[list, tuple]) -> list:
    """Flattening generic method for various usages.

    """
    while any([isinstance(x, (list, tuple)) for x in l]):
        temp = []
        for x in l:
            temp += x if isinstance(x, (list, tuple)) else [x]
        l = temp
    return list(l)

def isofclass(cls: Union[type, _GenericAlias], type_: Union[type, _GenericAlias]) -> bool:
    """An alternative of the `issubclass` function which
    works with any `typing._GenericAlias` type.
    Useful for more complex class checking.

    """
    if type(cls) == _GenericAlias:
        if hasattr(type_, "__origin__") and cls.__origin__ == type_.__origin__:
            if len(cls.__args__) != len(type_.__args__):
                return False

            for c_arg, t_arg in zip(cls.__args__, type_.__args__):
                if not issubclass(c_arg, t_arg):
                    return False

            return True

        return False
    elif type(type_) == _GenericAlias:
        return False
    else:
        return issubclass(cls, type_)

def isoftype(instance: Any, type_: Union[type, _GenericAlias]) -> bool:
    """An alternative of the `isinstance` function which
    works with any `typing._GenericAlias` type.
    Useful for more complex type checking.

    """
    if type(type_) == _GenericAlias:
        if isinstance(instance, type_.__origin__):
            if all(isinstance(x, type_.__args__) for x in instance):
                return True

        return False
    else:
        return isinstance(instance, type_)
