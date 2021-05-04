############################################# IMPORTS #############################################
#################### DISCORD ####################
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
    Type,
    Union
)

from .objectify import Objectify
from .objectify import (
    dictify,
    objectify
)
from .objectify import (
    JSON_like_any,
    JSON_like_transposed as JSON_like
)

############################################# CLASSES #############################################

class Group:
    """Represents a single configuration file.

    Parameters
        file: `str`
            The path to config file
        defaults: Union[`list`, Dict[`str`, Any], List[`Objectify`], `Objectify`] = `{}`
            The default value if file doesn't exist

    """
    def __init__(
        self, file: str, defaults: JSON_like = Objectify(),
    ):
        self.file = file
        self._data = load(
            file,
            to_object=type(defaults),
            if_error=defaults
        )

    def __repr__(self) -> str:
        """Returns repr(self)"""
        return repr(self._data)

    def get(self) -> JSON_like:
        """Returns the config file data.

        Returns
            Union[List[`Objectify`], `Objectify`]
                Config file data

        """
        return self._data

    def set(self, data: JSON_like):
        """Overwrite previous data to new given value.

        Parameters
            data: Union[List[`Objectify`], `Objectify`]
                The data to set

        """
        write(self.file, data)
        self._data = data

class Config:
    """Represents a `Cog` configuration files tree.

    For example, `Config.guild(Guild)` will return the
    configuration file of `Cog` for the given `Guild`.

    Parameters
        cog: `Cog`
            The `Cog` to represent
        **defaults: Union[`list`, Dict[`str`, Any], List[`Objectify`], `Objectify`]
            The value to set to any new file created,
            if not provided, defaults to `{}`

            Supported keys: globals, guild, channel, role, user, member

            Example: `guild={'foo': []}` will initiate any new guild
            configuation file to `{'foo': []}`

    """
    GLOBALS = "globals"
    CHANNEL = "channel"
    GUILD = "guild"
    MEMBER = "member"
    ROLE = "role"
    USER = "user"

    EXTENSION = ".json"

    def __init__(
        self, cog: Cog, *,
        globals: JSON_like = Objectify(), channel: JSON_like = Objectify(),
        guild:   JSON_like = Objectify(), member:  JSON_like = Objectify(),
        role:    JSON_like = Objectify(), user:    JSON_like = Objectify()
    ):
        self.cog = cog.__class__.__name__

        self.defaults_globals(globals)
        self.defaults_channel(channel)
        self.defaults_guild(guild)
        self.defaults_member(member)
        self.defaults_role(role)
        self.defaults_user(user)

    def _clear_folder(self, *scopes: str, defaults: JSON_like = Objectify()):
        """Sets to default every `Group` in requested path.

        Parameters
            defaults: Union[list, Dict[str, Any]] = `{}`
                The default value to write
            *scopes: `str`
                The path keys to targeted folder

        """
        path_to_folder, files = self._get_folder(*scopes)
        for file in files:
            write(f"{path_to_folder}/{file}", defaults)

    def _get_all(self, *scopes: str, defaults: JSON_like = Objectify()) -> Dict[str, Group]:
        """Returns a dict composed of files names from requested directory
        as keys and `Group` corresponding to file as values.

        Parameters
            *scopes: `str`
                The path elements leading to directory

        Returns
            Dict[`str`, `Group`]

        """
        if not defaults:
            data_type = self._defaults_globals

        path_to_folder, files = self._get_folder(*scopes)

        paths = [f"{path_to_folder}/{file}" for file in files]
        groups = [Group(path, defaults=defaults) for path in paths]

        files_without_extension = [file[:-len(self.EXTENSION)] for file in files]
        return {f: g for f, g in zip(files_without_extension, groups)}

    def _get_file(self, *primary_keys: str, defaults: JSON_like = Objectify()) -> Group:
        """Returns the wanted configuration file according to given arguments,
        as a `Group` instance.

        Parameters
            *primary_keys: `str`
                The keys leading to configuration file
                Example: `self._get_file('foo', 'bar')` -> `'{self.cog}/foo/bar.json'`

        Returns
            `Group`
                The representation of config file

        """
        path = f"{self.cog}/"
        path += "/".join(primary_keys) if primary_keys else self.GLOBALS
        path += self.EXTENSION

        return Group(path, defaults=defaults)

    def _get_folder(self, *scopes: str) -> str and List[str]:
        """Returns path to folder and folder files names.
        If path doesn't exist, safely creates it and returns an empty files list.

        Parameters
            *scopes: `str`
                The path elements leading to directory
        
        Returns
            `str`
                Path to folder
            List[`str`]
                Folder files names

        """
        path_to_folder = f"{self.cog}/{'/'.join(map(str, scopes))}"

        try:
            files = os.listdir(path_to_folder)
            files = [file for file in files if file.endswith(self.EXTENSION)]
        except FileNotFoundError:
            mkdir_p(path_to_folder)
            files = list()

        return path_to_folder, files

    def defaults_globals(self, defaults: JSON_like):
        """Sets default value for global configuration files.

        Parameters
            defaults: Union[`list`, Dict[`str`, Any], List[`Objectify`], `Objectify`] = `{}`
                The default value to parse

        """
        self._defaults_globals = defaults

    def defaults_channel(self, defaults: JSON_like):
        """Sets default value for `GuildChannel` configuration files.

        Parameters
            defaults: Union[`list`, Dict[`str`, Any], List[`Objectify`], `Objectify`] = `{}`
                The default value to parse

        """
        self._defaults_channel = defaults

    def defaults_guild(self, defaults: JSON_like):
        """Sets default value for `Guild` configuration files.

        Parameters
            defaults: Union[`list`, Dict[`str`, Any], List[`Objectify`], `Objectify`] = `{}`
                The default value to parse

        """
        self._defaults_guild = defaults

    def defaults_member(self, defaults: JSON_like):
        """Sets default value for `Member` configuration files.

        Parameters
            defaults: Union[`list`, Dict[`str`, Any], List[`Objectify`], `Objectify`] = `{}`
                The default value to parse

        """
        self._defaults_member = defaults

    def defaults_role(self, defaults: JSON_like):
        """Sets default value for `Role` configuration files.

        Parameters
            defaults: Union[`list`, Dict[`str`, Any], List[`Objectify`], `Objectify`] = `{}`
                The default value to parse

        """
        self._defaults_role = defaults

    def defaults_user(self, defaults: JSON_like):
        """Sets default value for `User` configuration files.

        Parameters
            defaults: Union[`list`, Dict[`str`, Any], List[`Objectify`], `Objectify`] = `{}`
                The default value to parse

        """
        self._defaults_user = defaults

    def globals(self) -> Group:
        return self._get_file(defaults=self._defaults_globals)

    def channel(self, channel: GuildChannel) -> Group:
        """Returns the given `GuildChannel` `Group` for `self.cog`.

        Parameters
            channel: `GuildChannel`
                The `GuildChannel` to look for

        Returns
            `Group`
                The representation of `GuildChannel` configuration file

        """
        return self._get_file(
            self.CHANNEL,
            str(channel.id),

            defaults=self._defaults_channel
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
        return self._get_file(
            self.CHANNEL,
            str(channel_id),

            defaults=self._defaults_channel
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
        return self._get_file(
            self.GUILD,
            str(guild.id),

            defaults=self._defaults_guild
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
        return self._get_file(
            self.GUILD,
            str(guild_id),

            defaults=self._defaults_guild
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
        return self._get_file(
            self.MEMBER,
            str(member.guild.id),
            str(member.id),

            defaults=self._defaults_member
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
        return self._get_file(
            self.MEMBER,
            str(guild_id),
            str(member_id),

            defaults=self._defaults_member
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
        return self._get_file(
            self.ROLE,
            str(role.id),

            defaults=self._defaults_role
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
        return self._get_file(
            self.ROLE,
            str(role_id),

            defaults=self._defaults_role
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
        return self._get_file(
            self.USER,
            str(user.id),

            defaults=self._defaults_user
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
        return self._get_file(
            self.USER,
            str(user_id),

            defaults=self._defaults_user
        )

    def all_channels(self) -> Dict[int, Group]:
        """Returns a dict composed of `GuildChannel` ids as keys and
        `Group` corresponding to `GuildChannel` as values.

        Returns
            Dict[`int`, `Group`]

        """
        return {int(k): v for k, v in self._get_all(self.CHANNEL, defaults=self._defaults_channel).items()}

    def all_guilds(self) -> Dict[int, Group]:
        """Returns a dict composed of `Guild` ids as keys and
        `Group` corresponding to `Guild` as values.

        Returns
            Dict[`int`, `Group`]

        """
        return {int(k): v for k, v in self._get_all(self.GUILD, defaults=self._defaults_guild).items()}

    def all_members(self, guild: Guild) -> Dict[int, Group]:
        """Returns a dict composed of `Member` ids as keys and
        `Group` corresponding to `Member` as values.
        /!\ As A `Member` is part of a `Guild`, `Guild` must be provided.

        Parameters
            guild: `Guild`
                The `Guild`

        Returns
            Dict[`int`, `Group`]

        """
        return {int(k): v for k, v in self._get_all(self.MEMBER, guild.id, defaults=self._defaults_member).items()}

    def all_members_with_guild_id(self, guild_id: int) -> Dict[int, Group]:
        """Returns a dict composed of `Member` ids as keys and
        `Group` corresponding to `Member` as values.
        /!\ As A `Member` is part of a `Guild`, `Guild` id must be provided.

        Parameters
            guild_id: `int`
                The `Guild` id

        Returns
            Dict[`int`, `Group`]

        """
        return {int(k): v for k, v in self._get_all(self.MEMBER, guild_id, defaults=self._defaults_member).items()}

    def all_roles(self) -> Dict[int, Group]:
        """Returns a dict composed of `Role` ids as keys and
        `Group` corresponding to `Role` as values.

        Returns
            Dict[`int`, `Group`]

        """
        return {int(k): v for k, v in self._get_all(self.ROLE, defaults=self._defaults_role).items()}

    def all_users(self) -> Dict[int, Group]:
        """Returns a dict composed of `User` ids as keys and
        `Group` corresponding to `User` as values.

        Returns
            Dict[`int`, `Group`]

        """
        return {int(k): v for k, v in self._get_all(self.USER, defaults=self._defaults_user).items()}

    def clear_globals(self):
        """Sets to default every global `Group` for `self.cog`.

        """
        self._clear_folder(defaults=self._defaults_globals)

    def clear_channels(self):
        """Sets to default every `GuildChannel` `Group` for `self.cog`.

        """
        self._clear_folder(
            self.CHANNEL,
            defaults=self._defaults_channel
        )

    def clear_guilds(self):
        """Sets to default every `Guild` `Group` for `self.cog`.

        """
        self._clear_folder(
            self.GUILD,
            defaults=self._defaults_guild
        )

    def clear_members(self, guild: Guild):
        """Sets to default every `Member` `Group` for `self.cog`.
        /!\ As a `Member` is part of a `Guild`, the `Guild` needs to be
        provided.

        Parameters
            guild: `Guild` = None
                The guild to aim for

        """
        if guild:
            self._clear_folder(
                self.MEMBER,
                guild.id,
                
                defaults=self._defaults_member
            )

    def clear_members_with_guild_id(self, guild_id: int):
        """Sets to default every `Member` `Group` for `self.cog`.
        /!\ As a `Member` is part of a `Guild`, the `Guild` needs to be
        provided.

        Parameters
            guild: `Guild` = None
                The guild to aim for

        """
        if guild:
            self._clear_folder(
                self.MEMBER,
                guild_id,
                
                defaults=self._defaults_member
            )

    def clear_roles(self):
        """Sets to default every `Role` `Group` for `self.cog`.

        """
        self._clear_folder(
            self.ROLE,
            defaults=self._defaults_role
        )

    def clear_users(self):
        """Sets to default every `User` `Group` for `self.cog`.

        """
        self._clear_folder(
            self.USER,
            defaults=self._defaults_user
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
    path: str, if_error: Union[list, dict] = [], to_object: Type[JSON_like] = None
) -> JSON_like_any:
    """Loads data from file path, as a json data file.

    Parameters
        path: `str`
            Desired file location path
        if_error: Union[`list`, `dict`] = `[]`
            Value to return if file doesn't exist
        to_object: Union[List[`Objectify`], `Objectify`, `type`] = `None`
            Automatically casts data to type if given, or
            keeps data as a simple `dict` or `list`.

    Returns
        Union[List[`Objectify`], `Objectify`, `dict`, `list`]
            The extracted data from requested path

    """
    try:
        with open(path, 'r') as file:
            data = json.load(file)
    except FileNotFoundError or NotADirectoryError:
        write(path, if_error)
        data = if_error

    return objectify(data, to_object) if to_object else data

def write(path: str, data: JSON_like_any):
    """Writes data to path, as a json data file.

    Parameters
        path: `str`
            Desired file location path
        data: Union[`list`, `dict`, `Objectify`]
            The json-like data to write in file

    """
    with safe_open(path, 'w') as file:
        file.write(json.dumps(dictify(data)))

#def update_config(
#    value: Union[List[Objectify], Objectify, List[Any], Dict[Any, Any]],
#    config: Group, *attributes: str,
#):
#    """A general function for configuration file updating.
#
#    Parameters
#        config: `Group`
#            The config file to edit
#        attribute: `str`
#            The attribute to edit
#        value: `Union[List[Objectify], Objectify, List[Any], Dict[Any, Any]]`
#            The value to set
#
#    """
#    config_data = config.get()
#
#    if config.to_object:
#        config_data = dictify(config_data)
#        if is_objectify(value):
#            setattr(config_data, attribute, value)
#        else:
#            setattr(config_data, attribute, objectify(value))
#    else:
#        if is_objectify(value):
#            config_data[attribute] = dictify(value)
#        else:
#            config_data[attribute] = value
#
#    config.set(config_data)
