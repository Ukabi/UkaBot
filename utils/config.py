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
from .objectify import (
    dictify,
    objectify
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
        self, file: str, data_type: Union[List[Objectify], Objectify, list],
        defaults: Union[list, Dict[str, Any], List[Objectify], Objectify] = {},
    ):
        self.file = file
        self._data = load(
            file,
            to_object=data_type,
            if_error=defaults
        )

    def __repr__(self) -> str:
        """Returns repr(self)"""
        return repr(self._data)

    def get(self) -> Union[List[Objectify], Objectify]:
        """Returns the config file data.

        Returns
            Union[List[`Objectify`], `Objectify`]
                Config file data

        """
        return self._data

    def set(self, data: Union[List[Objectify], Objectify]):
        """Overwrite previous data to new given value.

        Parameters
            data: Union[List[`Objectify`], `Objectify`]
                The data to set

        """
        # preventing from useless conversions and disk usage, unless data is modified
        if data != self._data:
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
    # for defaults data
    GLOBALS = "globals"
    CHANNEL = "channel"
    GUILD = "guild"
    MEMBER = "member"
    ROLE = "role"
    USER = "user"

    # for defaults data type
    GLOBALS_TYPE = "globals_type"
    CHANNEL_TYPE = "channel_type"
    GUILD_TYPE = "guild_type"
    MEMBER_TYPE = "member_type"
    ROLE_TYPE = "role_type"
    USER_TYPE = "user_type"

    EXTENSION = ".json"

    def __init__(
        self, cog: Cog, *,

        globals: Union[list, dict, List[Objectify], Objectify] = {},
        globals_type: Union[List[Objectify], Objectify, list] = Objectify,

        channel: Union[list, dict, List[Objectify], Objectify] = {},
        channel_type: Union[List[Objectify], Objectify, list] = Objectify,

        guild: Union[list, dict, List[Objectify], Objectify] = {},
        guild_type: Union[List[Objectify], Objectify, list] = Objectify,

        member: Union[list, dict, List[Objectify], Objectify] = {},
        member_type: Union[List[Objectify], Objectify, list] = Objectify,

        role: Union[list, dict, List[Objectify], Objectify] = {},
        role_type: Union[List[Objectify], Objectify, list] = Objectify,

        user: Union[list, dict, List[Objectify], Objectify] = {},
        user_type: Union[List[Objectify], Objectify, list] = Objectify,
    ):
        self.cog = cog.__class__.__name__

        if globals and globals_type:
            self.defaults_globals(globals, globals_type)
        else:
            self._defaults_globals = {}
            self._type_globals = Objectify

        if channel and channel_type:
            self.defaults_channel(channel, channel_type)
        else:
            self._defaults_channel = {}
            self._type_channel = Objectify

        if guild and guild_type:
            self.defaults_guild(guild, guild_type)
        else:
            self._defaults_guild = {}
            self._type_guild = Objectify

        if member and member_type:
            self.defaults_member(member, member_type)
        else:
            self._defaults_member = {}
            self._type_member = Objectify

        if role and role_type:
            self.defaults_role(role, role_type)
        else:
            self._defaults_role = {}
            self._type_role = Objectify

        if user and user_type:
            self.defaults_user(user, user_type)
        else:
            self._defaults_user = {}
            self._type_user = Objectify

    def _clear_folder(
        self, *scopes: str, defaults: Union[List[Objectify], Objectify, list] = Objectify()
    ):
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

    def _get_file(
        self, *primary_keys: str, defaults: Union[List[Objectify], Objectify, list] = Objectify(),
        data_type: Union[List[Objectify], Objectify, list] = Objectify
    ) -> Group:
        """Returns the wanted configuration file according to given arguments,
        as a `Group` instance.

        Parameters
            *primary keys: List[`str`]
                The keys leading to configuration file
                Example: `self._get_file('foo', 'bar')` -> `'{self.cog}/foo/bar.json'`

        Returns
            `Group`
                The representation of config file

        """
        path = f"{self.cog}/"
        path += "/".join(primary_keys) if primary_keys else self.GLOBALS
        path += self.EXTENSION

        return Group(path, data_type=data_type, defaults=defaults)

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

    def defaults_globals(
        self, defaults: Union[list, Dict[str, Any], List[Objectify], Objectify],
        data_type: Union[List[Objectify], Objectify, list]
    ):
        """Sets default value for global configuration files.

        Parameters
            defaults: Union[`list`, Dict[`str`, Any], List[`Objectify`], `Objectify`] = `{}`
                The default value to parse

        """
        self._defaults_globals = objectify(defaults, data_type)
        self._type_globals = data_type

    def defaults_channel(
        self, defaults: Union[list, Dict[str, Any], List[Objectify], Objectify],
        data_type: Union[List[Objectify], Objectify, list]
    ):
        """Sets default value for `GuildChannel` configuration files.

        Parameters
            defaults: Union[`list`, Dict[`str`, Any], List[`Objectify`], `Objectify`] = `{}`
                The default value to parse

        """
        self._defaults_channel = objectify(defaults, data_type)
        self._type_channel = data_type

    def defaults_guild(
        self, defaults: Union[list, Dict[str, Any], List[Objectify], Objectify],
        data_type: Union[List[Objectify], Objectify, list]
    ):
        """Sets default value for `Guild` configuration files.

        Parameters
            defaults: Union[`list`, Dict[`str`, Any], List[`Objectify`], `Objectify`] = `{}`
                The default value to parse

        """
        self._defaults_guild = objectify(defaults, data_type)
        self._type_guild = data_type

    def defaults_member(
        self, defaults: Union[list, Dict[str, Any], List[Objectify], Objectify],
        data_type: Union[List[Objectify], Objectify, list]
    ):
        """Sets default value for `Member` configuration files.

        Parameters
            defaults: Union[`list`, Dict[`str`, Any], List[`Objectify`], `Objectify`] = `{}`
                The default value to parse

        """
        self._defaults_member = objectify(defaults, data_type)
        self._type_member = data_type

    def defaults_role(
        self, defaults: Union[list, Dict[str, Any], List[Objectify], Objectify],
        data_type: Union[List[Objectify], Objectify, list]
    ):
        """Sets default value for `Role` configuration files.

        Parameters
            defaults: Union[`list`, Dict[`str`, Any], List[`Objectify`], `Objectify`] = `{}`
                The default value to parse

        """
        self._defaults_role = objectify(defaults, data_type)
        self._type_role = data_type

    def defaults_user(
        self, defaults: Union[list, Dict[str, Any], List[Objectify], Objectify],
        data_type: Union[List[Objectify], Objectify, list]
    ):
        """Sets default value for `User` configuration files.

        Parameters
            defaults: Union[`list`, Dict[`str`, Any], List[`Objectify`], `Objectify`] = `{}`
                The default value to parse

        """
        self._defaults_user = objectify(defaults, data_type)
        self._type_user = data_type

    def globals(self) -> Group:
        return self._get_file(
            data_type=self._type_globals,
            defaults=self._defaults_globals
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
        return self._get_file(
            self.CHANNEL,
            str(channel.id),

            data_type=self._type_channel,
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

            data_type=self._type_channel,
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

            data_type=self._type_guild,
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

            data_type=self._type_guild,
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

            data_type=self._type_member,
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

            data_type=self._type_member,
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

            data_type=self._type_role,
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

            data_type=self._type_role,
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

            data_type=self._type_user,
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

            data_type=self._type_user,
            defaults=self._defaults_user
        )

    def get_all(
        self, *scopes: str, data_type: Union[List[Objectify], Objectify, list] = None
    ) -> Dict[str, Group]:
        """Returns a dict composed of files names from requested directory
        as keys and `Group` corresponding to file as values.

        Parameters
            *scopes: `str`
                The path elements leading to directory

        Returns
            Dict[`str`, `Group`]

        """
        if not data_type:
            data_type = self._type_globals

        path_to_folder, files = self._get_folder(*scopes)

        paths = [f"{path_to_folder}/{file}" for file in files]
        groups = [Group(path, data_type=data_type) for path in paths]

        files_without_extension = [file[:-len(self.EXTENSION)] for file in files]
        return {f: g for f, g in zip(files_without_extension, groups)}

    def get_all_channels(self) -> Dict[int, Group]:
        """Returns a dict composed of `GuildChannel` ids as keys and
        `Group` corresponding to `GuildChannel` as values.

        Returns
            Dict[`int`, `Group`]

        """
        return {int(k): v for k, v in self.get_all(self.CHANNEL, data_type=self._type_channel).items()}

    def get_all_guilds(self) -> Dict[int, Group]:
        """Returns a dict composed of `Guild` ids as keys and
        `Group` corresponding to `Guild` as values.

        Returns
            Dict[`int`, `Group`]

        """
        return {int(k): v for k, v in self.get_all(self.GUILD, data_type=self._type_guild).items()}

    def get_all_members(self, guild: Guild) -> Dict[int, Group]:
        """Returns a dict composed of `Member` ids as keys and
        `Group` corresponding to `Member` as values.
        /!\ As A `Member` is part of a `Guild`, `Guild` must be provided.

        Parameters
            guild: `Guild`
                The `Guild`

        Returns
            Dict[`int`, `Group`]

        """
        return {int(k): v for k, v in self.get_all(self.MEMBER, guild.id, data_type=self._type_member).items()}

    def get_all_members_with_guild_id(self, guild_id: int) -> Dict[int, Group]:
        """Returns a dict composed of `Member` ids as keys and
        `Group` corresponding to `Member` as values.
        /!\ As A `Member` is part of a `Guild`, `Guild` id must be provided.

        Parameters
            guild_id: `int`
                The `Guild` id

        Returns
            Dict[`int`, `Group`]

        """
        return {int(k): v for k, v in self.get_all(self.MEMBER, guild_id, data_type=self._type_member).items()}

    def get_all_roles(self) -> Dict[int, Group]:
        """Returns a dict composed of `Role` ids as keys and
        `Group` corresponding to `Role` as values.

        Returns
            Dict[`int`, `Group`]

        """
        return {int(k): v for k, v in self.get_all(self.ROLE, data_type=self._type_role).items()}

    def get_all_users(self) -> Dict[int, Group]:
        """Returns a dict composed of `User` ids as keys and
        `Group` corresponding to `User` as values.

        Returns
            Dict[`int`, `Group`]

        """
        return {int(k): v for k, v in self.get_all(self.USER, data_type=self._type_user).items()}

    def clear_globals(self):
        """Sets to default every global `Group` for `self.cog`.

        """
        self._clear_folder(
            defaults=self._defaults_globals
        )

    def clear_all_channels(self):
        """Sets to default every `GuildChannel` `Group` for `self.cog`.

        """
        self._clear_folder(
            self.CHANNEL,
            defaults=self._defaults_channel
        )

    def clear_all_guilds(self):
        """Sets to default every `Guild` `Group` for `self.cog`.

        """
        self._clear_folder(
            self.GUILD,
            defaults=self._defaults_guild
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
            self._clear_folder(
                self.MEMBER,
                guild.id,
                
                defaults=self._defaults_member
            )

    def clear_all_roles(self):
        """Sets to default every `Role` `Group` for `self.cog`.

        """
        self._clear_folder(
            self.ROLE,
            defaults=self._defaults_role
        )

    def clear_all_users(self):
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
    path: str, if_error: Union[list, dict] = [],
    to_object: Union[List[Objectify], Objectify, type] = None
) -> Union[List[Objectify], Objectify, dict, list]:
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

def write(path: str, data: Union[List[Objectify], Objectify, dict, list]):
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
