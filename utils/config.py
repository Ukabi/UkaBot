############################################# IMPORTS #############################################
from discord import (
    Guild,
    Member,
    Role,
    User
)
from discord.abc import GuildChannel
from discord.ext.commands import Cog

##################### UTILS #####################
import errno
import json
import os
from typing import (
    Any,
    Dict,
    List,
    Union
)

from .objectify import Objectify
from .objectify import str_key_dict

############################################# CLASSES #############################################

class Group:
    """Represents a single configuration file.

    Parameters
        file: `str`
            The path to config file
        defaults: `Union[List[Any], Dict[str, Any]] = {}`
            The default value if file doesn't exist
        to_object: `bool = False`
            Determines if the `Group.data` attribute is either an
            `Union[List[Objectify], Objectify]` instance or an
            `Union[List[Any], Dict[str, Any]]` instance

    """
    def __init__(
        self, file: str, defaults: Union[List[Any], Dict[str, Any]] = {},
        to_object: bool = False
    ):
        self.file = file
        self.data = load(
            self.file,
            if_error=defaults,
            to_object=to_object
        )

    def __repr__(self):
        return str(Objectify.dictify(self.data))

    def get(self) -> Union[List[Objectify], Objectify, List[Any], Dict[str, Any]]:
        """Returns the config file data.

        Returns
            `Union[List[Objectify], Objectify, List[Any], Dict[str, Any]]`
                Config file data
                Instance of `Union[List[Objectify], Objectify]` if
                `Group.to_object` is set to `True`, else instance of
                `Union[List[Any], Dict[str, Any]]`

        """
        return self.data

    def set(
        self, data: Union[List[Objectify], Objectify, List[Any], Dict[Any, Any]]
    ):
        """Overwrite previous data to new given value.

        Parameters
            data: `Union[List[Objectify], Objectify, List[Any], Dict[Any, Any]]`
                The data to set

        """
        write(self.file, data)
        self.data = data

class Config:
    """Represents a `Cog` configuration files tree.

    For example, `Config.guild(Guild)` will return the
    configuration file of `Cog` for the given `Guild`.

    Parameters
        cog: `Cog`
            The `Cog` to represent
        to_object: `bool = False`
            Determines if the `Group.data` attribute is either an
            `Union[List[`Objectify`], `Objectify`]` instance or an
            `Union[List[Any], Dict[str, Any]]` instance
        **defaults: `Dict[str, Union[List[Any], Dict[str, Any]]]`
            The value to set to any new file created, if not
            provided, defaults to `{}`
            Supported key arguments : globals, guild, channel, role,
            user, member
            Example: `guild={'foo': []}` will initiate any new guild
            configuation file to `{'foo': []}`

    """
    GLOBALS = "globals"
    GUILD = "guild"
    CHANNEL = "channel"
    ROLE = "role"
    USER = "user"
    MEMBER = "member"

    EXTENTION = ".json"

    def __init__(
        self, cog: Cog = None, to_object: bool = False,
        **defaults: Dict[str, Union[List[Any], Dict[str, Any]]]
    ):
        if not cog or not isinstance(cog, Cog):
            raise NameError('Cog must be provided')
        else:
            self.cog = cog.__class__.__name__
            self.to_object = to_object

            self.defaults_globals(defaults.pop(self.GLOBALS, {}))
            self.defaults_guild(defaults.pop(self.GUILD, {}))
            self.defaults_channel(defaults.pop(self.CHANNEL, {}))
            self.defaults_role(defaults.pop(self.ROLE, {}))
            self.defaults_user(defaults.pop(self.USER, {}))
            self.defaults_member(defaults.pop(self.MEMBER, {}))

    def defaults_globals(self, defaults: Union[List[Any], Dict[str, Any]] = {}):
        """Sets default value for global configuration files.

        Parameters
            defaults: `Union[List[Any], Dict[str, Any]] = {}`
                The default value to parse

        """
        self.defaults = defaults

    def defaults_guild(self, defaults: Union[List[Any], Dict[str, Any]] = {}):
        """Sets default value for `Guild` configuration files.

        Parameters
            defaults: `Union[List[Any], Dict[str, Any]] = {}`
                The default value to parse

        """
        self.defaults_g = defaults

    def defaults_channel(self, defaults: Union[List[Any], Dict[str, Any]] = {}):
        """Sets default value for `GuildChannel` configuration files.

        Parameters
            defaults: `Union[List[Any], Dict[str, Any]] = {}`
                The default value to parse

        """
        self.defaults_c = defaults

    def defaults_role(self, defaults: Union[List[Any], Dict[str, Any]] = {}):
        """Sets default value for `Role` configuration files.

        Parameters
            defaults: `Union[List[Any], Dict[str, Any]] = {}`
                The default value to parse

        """
        self.defaults_r = defaults

    def defaults_user(self, defaults: Union[List[Any], Dict[str, Any]] = {}):
        """Sets default value for `User` configuration files.

        Parameters
            defaults: `Union[List[Any], Dict[str, Any]] = {}`
                The default value to parse

        """
        self.defaults_u = defaults

    def defaults_member(self, defaults: Union[List[Any], Dict[str, Any]] = {}):
        """Sets default value for `Member` configuration files.

        Parameters
            defaults: `Union[List[Any], Dict[str, Any]] = {}`
                The default value to parse

        """
        self.defaults_m = defaults

    def get_file(
        self, *primary_keys: str, defaults: Union[List[Any], Dict[str, Any]] = {}
    ) -> Group:
        """Returns the wanted configuration file according to given arguments,
        as a `Group` instance.

        Parameters
            *primary keys: `List[str]`
                The keys leading to configuration file
                Example: `self.get_file('foo', 'bar') -> '{self.cog}/foo/bar.json'`

        Returns
            `Group`
                The representation of config file

        """
        path = f"{self.cog}/"
        path += "/".join(primary_keys) if primary_keys else self.GLOBALS
        path += self.EXTENTION

        return Group(
            path,
            defaults=defaults,
            to_object=self.to_object
        )

    def globals(self) -> Group:
        return self.get_file(
            defaults=self.defaults
        )

    def guild(self, guild: Guild) -> Group:
        """Returns the given `Guild` `Group` for `self.cog`.

        Parameters
            guild: `Guild`
                The `Guild` to look for

        Returns
            `Group`
                The representation of `Guild` configuration file

        """
        return self.get_file(
            self.GUILD,
            str(guild.id),

            defaults=self.defaults_g
        )

    def guild_from_id(self, guild_id: int) -> Group:
        """Returns the given `Guild` `Group` for `self.cog`.

        Parameters
            guild_id: `int`
                The `Guild` id to look for

        Returns
            `Group`
                The representation of `Guild` configuration file

        """
        return self.get_file(
            self.GUILD,
            str(guild_id),

            defaults=self.defaults_g
        )

    def channel(self, channel: GuildChannel) -> Group:
        """Returns the given `GuildChannel` `Group` for `self.cog`.

        Parameters
            channel: `GuildChannel`
                The `GuildChannel` to look for

        Returns
            `Group`
                The representation of `GuildChannel` configuration file

        """
        return self.get_file(
            self.CHANNEL,
            str(channel.id),

            defaults=self.defaults_c
        )

    def channel_from_id(self, channel_id: int) -> Group:
        """Returns the given `GuildChannel` `Group` for `self.cog`.

        Parameters
            channel_id: `int`
                The `GuildChannel` id to look for

        Returns
            `Group`
                The representation of `GuildChannel` configuration file

        """
        return self.get_file(
            self.CHANNEL,
            str(channel_id),

            defaults=self.defaults_c
        )

    def role(self, role: Role) -> Group:
        """Returns the given `Role` `Group` for `self.cog`.

        Parameters
            role: `Role`
                The `Role` to look for

        Returns
            `Group`
                The representation of `Role` configuration file

        """
        return self.get_file(
            self.ROLE,
            str(role.id),

            defaults=self.defaults_r
        )

    def role_from_id(self, role_id: int) -> Group:
        """Returns the given `Role` `Group` for `self.cog`.

        Parameters
            role_id: `int`
                The `Role` id to look for

        Returns
            `Group`
                The representation of `Role` configuration file

        """
        return self.get_file(
            self.ROLE,
            str(role_id),

            defaults=self.defaults_r
        )

    def user(self, user: User) -> Group:
        """Returns the given `User` `Group` for `self.cog`.

        Parameters
            user: `User`
                The `User` to look for

        Returns
            `Group`
                The representation of `User` configuration file

        """
        return self.get_file(
            self.USER,
            str(user.id),

            defaults=self.defaults_u
        )

    def user_from_id(self, user_id: int) -> Group:
        """Returns the given `User` `Group` for `self.cog`.

        Parameters
            user_id: `int`
                The `User` id to look for

        Returns
            `Group`
                The representation of `User` configuration file

        """
        return self.get_file(
            self.USER,
            str(user_id),

            defaults=self.defaults_u
        )

    def member(self, member: Member) -> Group:
        """Returns the given `Member` `Group` for `self.cog`.

        Parameters
            member: `Member`
                The `Member` to look for

        Returns
            `Group`
                The representation of `Member` configuration file

        """
        return self.get_file(
            self.MEMBER,
            str(member.guild.id),
            str(member.id),

            defaults=self.defaults_m
        )

    def member_from_ids(self, guild_id: int, member_id: int) -> Group:
        """Returns the given `Member` `Group` for `self.cog`.
        /!\ A `Member` is a `User` associated to a `Guild`, so both IDs
        are required.

        Parameters
            guild_id: `int`
                The `Guild` id to look for
            member_id: `int`
                The `Union[User, Member]` id to look for

        Returns
            `Group`
                The representation of `Member` configuration file

        """
        return self.get_file(
            self.MEMBER,
            str(guild_id),
            str(member_id),

            defaults=self.defaults_m
        )

    def get_folder(self, *scopes: str) -> str and List[str]:
        """Returns path to folder and folder files names.
        If path doesn't exist, safely creates it and returns an empty files list.

        Parameters
            *scopes: `str`
                The path elements leading to directory
        
        Returns
            `str`
                Path to folder
            `List[str]`
                Folder files names

        """
        path_to_folder = f"{self.cog}/{'/'.join(scopes)}"

        try:
            files = os.listdir(path_to_folder)
            files = [file for file in files if file.endswith(self.EXTENTION)]
        except FileNotFoundError:
            mkdir_p(path_to_folder)
            files = list()

        return path_to_folder, files

    def get_all(self, *scopes: str) -> Dict[str, Group]:
        """Returns a dict composed of files names from requested directory
        as keys and `Group` corresponding to file as values.

        Parameters
            *scopes: `str`
                The path elements leading to directory

        Returns
            `Dict[str, Group]`

        """
        path_to_folder, files = self.get_folder(*scopes)

        paths = [f"{path_to_folder}/{file}" for file in files]
        groups = [Group(path, to_object=self.to_object) for path in paths]

        files_without_extention = [file[:-len(self.EXTENTION)] for file in files]
        return {f: g for f, g in zip(files_without_extention, groups)}

    def get_all_guilds(self) -> Dict[int, Group]:
        """Returns a dict composed of `Guild` ids as keys and
        `Group` corresponding to `Guild` as values.

        Returns
            `Dict[int, Group]`

        """
        return {int(k): v for k, v in self.get_all(self.GUILD).items()}

    def get_all_channels(self) -> Dict[int, Group]:
        """Returns a dict composed of `GuildChannel` ids as keys and
        `Group` corresponding to `GuildChannel` as values.

        Returns
            `Dict[int, Group]`

        """
        return {int(k): v for k, v in self.get_all(self.CHANNEL).items()}

    def get_all_roles(self) -> Dict[int, Group]:
        """Returns a dict composed of `Role` ids as keys and
        `Group` corresponding to `Role` as values.

        Returns
            `Dict[int, Group]`

        """
        return {int(k): v for k, v in self.get_all(self.ROLE).items()}

    def get_all_users(self) -> Dict[int, Group]:
        """Returns a dict composed of `User` ids as keys and
        `Group` corresponding to `User` as values.

        Returns
            `Dict[int, Group]`

        """
        return {int(k): v for k, v in self.get_all(self.USER).items()}

    def get_all_members(self, guild: Guild) -> Dict[int, Group]:
        """Returns a dict composed of `Member` ids as keys and
        `Group` corresponding to `Member` as values.
        /!\ As A `Member` is part of a `Guild`, `Guild` must be provided.

        Parameters
            guild: `Guild`
                The `Guild`

        Returns
            `Dict[int, Group]`

        """
        return {int(k): v for k, v in self.get_all(self.MEMBER, guild.id).items()}

    def get_all_members_with_guild_id(self, guild_id: int) -> Dict[int, Group]:
        """Returns a dict composed of `Member` ids as keys and
        `Group` corresponding to `Member` as values.
        /!\ As A `Member` is part of a `Guild`, `Guild` id must be provided.

        Parameters
            guild_id: `int`
                The `Guild` id

        Returns
            `Dict[int, Group]`

        """
        return {int(k): v for k, v in self.get_all(self.MEMBER, guild_id).items()}

    def clear_folder(
        self, *scopes: str, defaults: Union[List[Any], Dict[str, Any]] = {}
    ):
        """Sets to default every `Group` in requested path.

        Parameters
            defaults: `Union[List[Any], Dict[str, Any]] = {}`
                The default value to write
            *scopes: `str`
                The path keys to targeted folder

        """
        path_to_folder, files = self.get_folder(*scopes)
        for file in files:
            write(f"{path_to_folder}/{file}", defaults)

    def clear_globals(self):
        """Sets to default every global `Group` for `self.cog`.

        """
        self.clear_folder(
            defaults=self.defaults
        )

    def clear_all_guilds(self):
        """Sets to default every `Guild` `Group` for `self.cog`.

        """
        self.clear_folder(
            self.GUILD,
            defaults=self.defaults_g
        )

    def clear_all_channels(self):
        """Sets to default every `GuildChannel` `Group` for `self.cog`.

        """
        self.clear_folder(
            self.CHANNEL,
            defaults=self.defaults_c
        )

    def clear_all_roles(self):
        """Sets to default every `Role` `Group` for `self.cog`.

        """
        self.clear_folder(
            self.ROLE,
            defaults=self.defaults_r
        )

    def clear_all_users(self):
        """Sets to default every `User` `Group` for `self.cog`.

        """
        self.clear_folder(
            self.USER,
            defaults=self.defaults_u
        )

    def clear_all_members(self, guild: Guild = None):
        """Sets to default every `Member` `Group` for `self.cog`.
        /!\ As a `Member` is part of a `Guild`, the `Guild` needs to be
        provided.

        Parameters
            guild: `Guild` = None
                The guild to aim for

        """
        if guild:
            self.clear_folder(
                self.MEMBER,
                guild.id,
                
                defaults=self.defaults_m
            )

############################################ FUNCTIONS ############################################

def mkdir_p(path: str):
    """Safely creates path to desired location if it doesn't exist.

    Parameters
        path: `str`
            The path to desired location

    """
    if path:
        try:
            os.makedirs(path)
        except OSError as exc:
            if exc.errno == errno.EEXIST and os.path.isdir(path):
                pass
            else:
                raise OSError("Couldn't create file or directory.")

def safe_open(path: str, mode: str) -> open:
    """Same as the `open` function, but safely creates file before.

    """
    mkdir_p(os.path.dirname(path))
    return open(path, mode=mode)

def load(
    path: str, if_error: Union[list, dict] = [], to_object: bool = False
    ) -> Union[List[Objectify], Objectify, List[Any], Dict[str, Any]]:
    """Loads data from file path, as a json data file.

    Parameters
        path: `str`
            Desired file location path
        if_error: `Union[list, dict] = []`
            Value to return if file doesn't exist
        to_object: `bool = False`
            Automatically casts data to an `Objectify` or `List[Objectify]` object if
            `True`, or keeps data as a simple `Dict[str, Any]` or `List[Any]` if `False`
    
    Returns
        `Union[List[Objectify], Objectify, List[Any], Dict[str, Any]]`
            The extracted data from requested path

    """
    try:
        with open(path, 'r') as file:
            data = json.load(file)
    except FileNotFoundError or NotADirectoryError:
        write(path, if_error)
        data = if_error
    return Objectify.objectify(data) if to_object else data

def write(
    path: str,
    data: Union[List[Objectify], Objectify, List[Any], Dict[str, Any]]
):
    """Writes data to path, as a json data file.

    Parameters
        path: `str`
            Desired file location path
        data: `Union[List[Objectify], Objectify, List[Any], Dict[str, Any]]`
            The data to write in file

    """
    data = Objectify.dictify(data)
    data = str_key_dict(data) if isinstance(data, dict) else data
    with safe_open(path, 'w') as file:
        file.write(json.dumps(data))
