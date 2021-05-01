############################################# IMPORTS #############################################

from typing import (
    _GenericAlias,
    Any,
    Callable,
    Dict,
    List,
    Tuple,
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

def flatten(l: Union[list, tuple]) -> list:
    """Flattening generic method for various usages.

    """
    while any([isinstance(x, (list, tuple)) for x in l]):
        temp = []
        for x in l:
            temp += x if isinstance(x, (list, tuple)) else [x]
        l = temp
    return list(l)

def isofclass(
    cls: Union[type, _GenericAlias],
    type_or_tuple: Union[type, _GenericAlias, Tuple[Union[type, _GenericAlias]]]
) -> bool:
    """An alternative of the `issubclass` function which
    works with any `typing._GenericAlias` type.
    Useful for more complex class checking.

    """
    # converting type parameter to tuple if single value given
    if isinstance(type_or_tuple, tuple):
        types = type_or_tuple
    else:
        types = (type_or_tuple,)

    # verifying if cls is a subclass of at least one of given classes
    for type_ in types:
        # typing class case
        if type(cls) == _GenericAlias:
            # cls and type_ have same base
            if hasattr(type_, "__origin__") and cls.__origin__ == type_.__origin__:
                # cls and type_ have same arguments length
                if len(cls.__args__) == len(type_.__args__):
                    for c_arg, t_arg in zip(cls.__args__, type_.__args__):
                        # cls arguments are subclass of at least one type_ subclass, so True
                        if isofclass(c_arg, t_arg):
                            return True

        # else cls is a common class, so if cls isn't typing class
        elif type(type_) != _GenericAlias:
            # and cls is subclass of type_, then True
            if issubclass(cls, type_):
                return True

    # every other case if False
    return False

def isoftype(
    instance: Any, type_or_tuple: Union[type, _GenericAlias, Tuple[Union[type, _GenericAlias]]]
) -> bool:
    """An alternative of the `isinstance` function which
    works with any `typing._GenericAlias` type.
    Useful for more complex type checking.

    """
    # converting type parameter to tuple if single value given
    if isinstance(type_or_tuple, tuple):
        types = type_or_tuple
    else:
        types = (type_or_tuple,)

    # verifying if instance is an instance of at least one of given classes
    for type_ in types:
        # typing class case
        if type(type_) == _GenericAlias:
            # instance has same base
            if isoftype(instance, type_.__origin__):
                # all instance components have same type as type_ arguments, so True
                if all(isoftype(x, type_.__args__) for x in instance):
                    return True

        # else type_ is a common class, so basic isinstance checking
        elif isinstance(instance, type_):
            return True

    # every other case if False
    return False
