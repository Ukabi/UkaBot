############################################# IMPORTS #############################################

from typing import (
    Any,
    Iterable,
    List,
    Union
)
from .utils import (
    isofclass,
    isoftype
)

############################################# CLASSES #############################################

class Objectify:
    """A more intuitive way to manipulate json-like dicts.
    Transforms any json-like `dict` into a both key and
    attribute-oriented class.
    This class is meant to have children, in which constructor
    takes class attributes as parameters, so that attribute
    type is always defined and unique.

    /!\ SUBCLASS MUST BE ANNOTATED WITH ATTRIBUTES AND
    THEIR TYPES, ELSE CONVERSION FROM Union[`dict`, `list`]
    TO Union[`D`, List[`D`]] WILL NEVER WORK.

    Example annotation format:
        class A(D):
            b: B
            def __init__(self, b: B):
                super().__init__(b=b)

        class B(D):
            c: List[C]
            def __init__(self, c: List[C]):
                super().__init__(c=c)

        class C(D):
            d: int
            def __init__(self, d: int):
                super().__init__(d=d)

    Considering the above configuration, both syntaxes are
    equivalent: A['b'][0]['d'] <==> A.b[0].d

    """
    __annotations__ = {}

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __contains__(self, key: str) -> bool:
        """Returns key in self"""
        return key in self.keys()

    def __eq__(self, value: Any) -> bool:
        """Returns self == value"""
        return self._compile() == value

    def __getitem__(self, key: str) -> Any:
        """Returns self[key] (<==> self.key)"""
        return getattr(self, key)

    def __iter__(self) -> Iterable:
        """Returns iter(self)"""
        for key, value in self.items():
            if isinstance(value, Objectify):
                yield (key, dict(iter(value)))
            else:
                yield (key, value)

    def __len__(self) -> int:
        """Returns len(self)"""
        return len(self.keys())

    def __ne__(self, value: Any) -> bool:
        """Returns self != value"""
        return not self.__eq__(value)

    def __repr__(self) -> str:
        """Returns repr(self)"""
        return repr(self._compile())

    def __setitem__(self, key: str, value: Any):
        """Affects value to self[key] (hence self.key)"""
        if hasattr(self, key):
            setattr(self, key, value)
        else:
            raise AttributeError

    def _compile(self) -> dict:
        """Compiles self in a dict structure"""
        d = {}
        for key, value in self.items():
            if isinstance(value, Objectify):
                d[key] = value._compile()
            else:
                d[key] = value

        return d

    def copy(self) -> "Objectify":
        """Same as dict.copy()"""
        d = {}
        for key, value in self.items():
            if isinstance(value, Objectify):
                d[key] = value.copy()
            else:
                d[key] = value
        return self.__class__(**d)

    def items(self) -> Iterable:
        """Same as dict.items()"""
        return self.__dict__.items()
    
    def keys(self) -> Iterable:
        """Same as dict.keys()"""
        return self.__dict__.keys()

    def values(self) -> Iterable:
        """Same as dict.values()"""
        return self.__dict__.values()

def objectify(
    iterable: Union[list, dict], cls: Union[List[Objectify], Objectify, Any]
) -> Union[List[Objectify], Objectify, Any]:
    """Transforms any json-like `dict` into a both key and
    attribute-oriented class.

    Parameters
        iterable: Union[`list`, `dict`]
            The instance to convert
        cls: Union[List[`Objectify`], `Objectify`, Any]
            The type to convert instance to

    Returns
        Union[List[`Objectify`], `Objectify`, Any]
            The converted instance to correct type
    
    Raises
        AttributeError
        TypeError

    """
    if isinstance(iterable, list) and isofclass(cls, List[Objectify]):
        return [objectify(x, cls.__args__[0]) for x in iterable]

    elif isinstance(iterable, dict) and isofclass(cls, Objectify):
        args = {}
        for arg, c in cls.__annotations__.items():
            if isofclass(c, Objectify):
                args[arg] = objectify(iterable[arg], c)
            elif isofclass(c, List[Objectify]):
                args[arg] = [objectify(x, c.__args__[0]) for x in iterable[arg]]
            else:
                args[arg] = iterable[arg]

        return cls(**args)

    elif isoftype(iterable, cls):
        return iterable

    else:
        raise TypeError("Mismatch. Conversion pattern and data pattern don't seem alike.")

    # Just for the fun of it
    # return [objectify(x, cls.__args__[0]) for x in iterable] if isinstance(iterable, list) and isofclass(cls, List[Objectify]) else {arg: objectify(iterable[arg], c) if isofclass(c, Objectify) else [objectify(x, c.__args__[0]) for x in iterable[arg]] if isofclass(c, List[Objectify]) else iterable[arg] for arg, c in cls.__annotations__.items()} if isinstance(iterable, dict) and isofclass(cls, Objectify) else iterable
