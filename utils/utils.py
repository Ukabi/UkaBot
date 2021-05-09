############################################# IMPORTS #############################################

from typing import (
    _GenericAlias,
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    Set,
    Tuple,
    Type,
    Union
)
from typing import (
    get_args,
    get_origin
)

############################################# GLOBALS #############################################

ExtendedType = Union[type, _GenericAlias]
One_D_Iterable = Union[list, tuple, set, frozenset]

############################################# CLASSES #############################################

class ImprovedList(list):
    """Some useful functions to explore or transform list content
    more easily.

    """

    def index(
        self, v: Any, *, start: int = 0, stop: int = 9223372036854775807,
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
        self, v: Any, *, start: int = 0, stop: int = 9223372036854775807,
        key: Callable = lambda x: x
    ) -> Any:
        """Just like `list.__getitem__`, but admits a customizable key
        for easier searches.

        """
        return self[self.index(v=v, start=start, stop=stop, key=key)]

    def lexsort(self, key: Callable=None, reverse: bool=False):
        """Same as `list.sort`, but applies lexical sort instead."""
        self[:] = lexsorted(self, key=key, reverse=reverse)

############################################ FUNCTIONS ############################################

def flatten(l: One_D_Iterable) -> list:
    """Flattening generic method for various usages."""
    while any([isinstance(x, get_args(One_D_Iterable)) for x in l]):
        temp = []
        for x in l:
            temp += x if isinstance(x, get_args(One_D_Iterable)) else [x]
        l = temp
    return list(l)

def isofclass(
    cls: ExtendedType, type_or_tuple: Type[Union[ExtendedType, Tuple[ExtendedType]]]
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
        # if both are typing classes
        if type(cls) == _GenericAlias and type(type_) == _GenericAlias:
            (cls_args, cls_origin) = (get_args(cls), get_origin(cls))
            (type_args, type_origin) = (get_args(type_), get_origin(type_))

            # cls and type_ have same base and same length
            if cls_origin == type_origin and len(cls_args) == len(type_args):
                for c_arg, t_arg in zip(cls_args, type_args):
                    # cls arguments are subclass of at least one type_ subclass, so True
                    if isofclass(c_arg, t_arg):
                        return True

        # else if both are common classes
        elif type(cls) != _GenericAlias and type(type_) != _GenericAlias:
            # and cls is subclass of type_, then True
            if issubclass(cls, type_):
                return True

    # every other case if False
    return False

def isoftype(instance: Any, type_or_tuple: Type[Union[ExtendedType, Tuple[ExtendedType]]]) -> bool:
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
            if isoftype(instance, get_origin(type_)):
                # all instance components have same type as type_ arguments, so True
                if all(isoftype(x, get_args(type_)) for x in instance):
                    return True

        # else type_ is a common class, so basic isinstance checking
        elif isinstance(instance, type_):
            return True

    # every other case if False
    return False

def lexsorted(iterable: One_D_Iterable, *, key: Callable=None, reverse: bool=False):
    """Roughly equivalent to `sorted`, but applies lexical sort instead."""
    key_values = [key(x) if key else x for x in iterable]
    order = sorted(
        range(len(key_values)),
        key=key_values.__getitem__,
        reverse=reverse
    )

    return [iterable[i] for i in order]

def revert_dict(d: Dict[Any, One_D_Iterable]) -> Dict[Any, Set[Any]]:
    """Exchanges keys and values from provided `dict`."""
    if d:
        values = set.union(*(d.values()))
        return {v: {k for k, vs in d.items() if v in vs} for v in values}
    else:
        return {}
