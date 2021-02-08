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
            `Union[List[`Objectify`], `Objectify`]` instance or an
            `Union[List[Any], Dict[str, Any]]` instance

    """

    def __init__(self, file: str, defaults: Union[List[Any], Dict[str, Any]] = {},
                 to_object: bool = False):
        self.file = file
        self.data = load(
            self.file,
            if_error=defaults,
            to_object=to_object
        )

    def get(self) -> Union[List[Objectify], Objectify, List[Any], Dict[str, Any]]:
        """Returns the config file data.

        Returns
            `Union[List[Objectify], Objectify, List[Any], Dict[str, Any]]`
                Config file data
                Instance of `Union[List[`Objectify`], `Objectify`]` if
                `Group.to_object` is set to `True`, else instance of
                `Union[List[Any], Dict[str, Any]]`

        """
        return self.data

    def set(self,
            data: Union[List[Objectify], Objectify, List[Any], Dict[str, Any]]
    ):
        """Overwrite previous data to new given value.

        Parameters
            data: `Union[List[Objectify], Objectify, List[Any], Dict[str, Any]]`
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
            Supported key arguments : global, guild, channel, role,
            user, member
            Example: `guild={'foo': []}` will initiate any new guild
            configuation file to `{'foo': []}`

    """
    GLOBAL = "global"
    GUILD = "guild"
    CHANNEL = "channel"
    ROLE = "role"
    USER = "user"
    MEMBER = "member"

    def __init__(self, cog: Cog = None, to_object: bool = False,
                 **defaults: Dict[str, Union[List[Any], Dict[str, Any]]]):
        if not cog or not isinstance(cog, Cog):
            raise NameError('Cog must be provided')
        else:
            self.cog = cog.__class__.__name__
            self.to_object = to_object

            self.defaults_global(defaults.pop(self.GLOBAL, {}))
            self.defaults_guild(defaults.pop(self.GUILD, {}))
            self.defaults_channel(defaults.pop(self.CHANNEL, {}))
            self.defaults_role(defaults.pop(self.ROLE, {}))
            self.defaults_user(defaults.pop(self.USER, {}))
            self.defaults_member(defaults.pop(self.MEMBER, {}))

    def defaults_global(self, defaults: Union[List[Any], Dict[str, Any]] = {}):
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

    def get_file(self, *primary_keys: str,
                 defaults: Union[List[Any], Dict[str, Any]] = {}) -> Group:
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
        path = f'{self.cog}/'
        path += self.GLOBAL if not primary_keys else "/".join(primary_keys)
        path += ".json"

        return Group(
            path,
            defaults=defaults,
            to_object=self.to_object
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

    def clear_folder(self, defaults: Union[List[Any], Dict[str, Any]] = {},
              *scopes: List[str]):
        """Sets to default every `Group` in requested path.

        Parameters
            defaults: `Union[List[Any], Dict[str, Any]] = {}`
                The default value to write
            *scopes: `List[str]`
                The path keys to targeted folder

        """
        folder = self.cog
        files = os.listdir(folder)
        for scope in scopes:
            folder += f'/{scope}'
            files = os.listdir(folder)
        files = [file for file in files if file.endswith('.json')]

        for file in files:
            write(f'{folder}/{file}', defaults)

    def clear_all(self):
        """Sets to default every `Group` for `self.cog`.

        """
        self.clear_all_globals()
        self.clear_all_guilds()
        self.clear_all_channels()
        self.clear_all_roles()
        self.clear_all_users()
        self.clear_all_members()

    def clear_all_globals(self):
        """Sets to default every global `Group` for `self.cog`.

        """
        self.clear_folder(self.defaults, self.GLOBAL)

    def clear_all_guilds(self):
        """Sets to default every `Guild` `Group` for `self.cog`.

        """
        self.clear_folder(self.defaults_g, self.GUILD)

    def clear_all_channels(self):
        """Sets to default every `GuildChannel` `Group` for `self.cog`.

        """
        self.clear_folder(self.defaults_c, self.CHANNEL)

    def clear_all_roles(self):
        """Sets to default every `Role` `Group` for `self.cog`.

        """
        self.clear_folder(self.defaults_r, self.ROLE)

    def clear_all_users(self):
        """Sets to default every `User` `Group` for `self.cog`.

        """
        self.clear_folder(self.defaults_u, self.USER)

    def clear_all_members(self, guild: Guild = None):
        """Sets to default every `Member` `Group` for `self.cog`.
        /!\ As a `Member` is part of a `Guild`, the `Guild` needs to be
        provided.

        Parameters
            guild: `Guild` = None
                The guild to aim for

        """
        if guild is not None:
            self.clear_folder(self.defaults_m, self.MEMBER, guild.id)
        else:
            self.clear_folder(self.defaults_m, self.MEMBER)

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

def load(path: str, if_error: Union[list, dict] = [],
         to_object: bool = False
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

def write(path: str,
          data: Union[List[Objectify], Objectify, List[Any], Dict[str, Any]]):
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
