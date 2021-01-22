############################################# IMPORTS #############################################

import errno
import json
import os
from typing import (
    Any,
    Dict,
    List,
    Union
)
from utils.Objectify import Objectify

############################################ FUNCTIONS ############################################

def mkdir_p(path: str):
    """Safely creates path to desired location if it doesn't exist.

    Parameters
        path: str
            The path to desired location

    """
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise OSError("Couldn't create file or directory.")

def safe_open(path: str, mode: str, buffering: int, encoding: str, errors: str, newline: str, closefd: bool, opener: callable) -> open:
    """Same as the `open` function, but safely creates file before.

    """
    mkdir_p(os.path.dirname(path))
    return open(
        path,
        mode=mode,
        buffering=buffering,
        encoding=encoding,
        errors=errors,
        newline=newline,
        closefd=closefd,
        opener=opener
    )

def load(path: str, if_error: Union[list, dict] = [], to_object: bool = False) -> Union[List[Objectify], Objectify, List[Any], Dict[str, Any]]:
    """Loads data from file path, as a json data file.

    Parameters
        path: str
            Desired file location path
        if_error: Union[list, dict] = []
            Value to return if file doesn't exist
        to_object: bool = False
            Automatically casts data to an `Objectify` or `List[Objectify]` object if True,
            or keeps data as a simple `Dict[str, Any]` or `List[Any]` if False
    
    Returns
        Union[List[Objectify], Objectify, List[Any], Dict[str, Any]]
            The extracted data from requested path

    """
    try:
        with open(path, 'r') as file:
            data = json.load(file)
    except FileNotFoundError or NotADirectoryError:
        with safe_open(path, 'w') as file:
            file.write(if_error)
        data = if_error
    return Objectify.objectify(data) if to_object else data

def write(path: str, data: Union[List[Objectify], Objectify, List[Any], Dict[str, Any]]):
    """Writes data to path, as a json data file.

    Parameters
        path: str
            Desired file location path
        data: Union[List[Objectify], Objectify, List[Any], Dict[str, Any]]
            The data to write in file

    """
    with safe_open(path, 'w') as file:
        file.write(json.dumps(Objectify.dictify(data)))