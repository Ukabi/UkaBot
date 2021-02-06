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
        file: str
            The path to config file
        defaults: Union[List[Any], Dict[str, Any]] = {}
            The default value if file doesn't exist
        to_object: bool = False
            Determines if the `Group.data` attribute is either an
            Union[List[`Objectify`], `Objectify`] instance or an
            Union[List[Any], Dict[str, Any]] instance

    """

    def __init__(self, file: str, defaults: Union[List[Any], Dict[str, Any]] = {}, to_object: bool = False):
        self.file = file
        self.data = load(
            self.file,
            if_error=defaults,
            to_object=to_object
        )

    def get(self) -> Union[List[Objectify], Objectify, List[Any], Dict[str, Any]]:
        """Returns the config file data.
        
        Returns
            Union[List[Objectify], Objectify, List[Any], Dict[str, Any]]
                Config file data
                Instance of Union[List[`Objectify`], `Objectify`] if Group.to_object is set to True,
                else instance of Union[List[Any], Dict[str, Any]]

        """
        return self.data

    def set(self, data: Union[List[Objectify], Objectify, List[Any], Dict[str, Any]]):
        """Overwrite previous data to new given value.

        Parameters
            data: Union[List[Objectify], Objectify, List[Any], Dict[str, Any]]
                The data to set

        """
        write(self.file, data)
        self.data = data

class Config:
    """Represents a `Cog` configuration files tree.

    For example, Config.guild(discord.Guild) will return the
    configuration file of `Cog` for the given `Guild`.

    Parameters
        cog: `discord.ext.commands.Cog`
            The `Cog` to represent
        defaults: Union[List[Any], Dict[str, Any]] = {}
            The value to set to any new file created
        to_object: bool = False
            Determines if the `Group.data` attribute is either an
            Union[List[`Objectify`], `Objectify`] instance or an
            Union[List[Any], Dict[str, Any]] instance

    """
    GLOBAL = "global"
    GUILD = "guild"
    CHANNEL = "channel"
    ROLE = "role"
    USER = "user"
    MEMBER = "member"

    def __init__(self, cog: Cog = None, defaults: Union[List[Any], Dict[str, Any]] = {}, to_object: bool = False):
        if not cog or not isinstance(cog, Cog):
            raise NameError('Cog must be provided')
        else:
            self.cog = cog.__class__.__name__
            self.defaults = defaults
            self.to_object = to_object

    def get_file(self, *primary_keys: str) -> Group:
        """Returns the wanted configuration file according to given arguments,
        as a `Group` instance.

        Parameters
            *primary keys: List[str]
                The keys that will lead to configuration file
                Example: self.get_file('foo', 'bar') -> '{self.cog}/foo/bar.json'
        
        Returns
            Group
                The representation of config file

        """
        file = f'{self.cog}/'
        file += GLOBAL if not primary_keys else "/".join(primary_keys)
        file += ".json"

        return Group(
            file,
            defaults=self.defaults,
            to_object=self.to_object
        )

    def guild(self, guild: Guild) -> Group:
        """Returns the given `discord.Guild` configuration file for self.cog.

        Parameters
            guild: `discord.Guild`
                The guild to look for
        
        Returns
            Group
                The representation of guild configuration file

        """
        return self.get_file(
            self.GUILD,
            str(guild.id)
        )

    def guild_from_id(self, guild_id: int) -> Group:
        """Returns the given `discord.Guild.id` configuration file for self.cog.

        Parameters
            guild: int
                The guild id to look for
        
        Returns
            Group
                The representation of guild configuration file

        """
        return self.get_file(
            self.GUILD,
            str(guild_id)
        )

    def channel(self, channel: GuildChannel) -> Group:
        """Returns the given `discord.GuildChannel` configuration file for self.cog.

        Parameters
            channel: GuildChannel
                The member to look for
        
        Returns
            Group
                The representation of channel configuration file

        """
        return self.get_file(
            self.CHANNEL,
            str(channel.id)
        )

    def channel_from_id(self, channel_id: int) -> Group:
        """Returns the given `discord.GuildChannel.id` configuration file for self.cog.

        Parameters
            channel_id: int
                The channel id to look for
        
        Returns
            Group
                The representation of channel configuration file

        """
        return self.get_file(
            self.CHANNEL,
            str(channel_id)
        )

    def role(self, role: Role) -> Group:
        """Returns the given `discord.Role` configuration file for self.cog.

        Parameters
            role: Role
                The member to look for
        
        Returns
            Group
                The representation of role configuration file

        """
        return self.get_file(
            self.ROLE,
            str(role.id)
        )

    def role_from_id(self, role_id: int) -> Group:
        """Returns the given `discord.Role.id` configuration file for self.cog.

        Parameters
            role_id: int
                The channel id to look for
        
        Returns
            Group
                The representation of role configuration file

        """
        return self.get_file(
            self.ROLE,
            str(role_id)
        )

    def user(self, user: User) -> Group:
        """Returns the given `discord.User` configuration file for self.cog.

        Parameters
            user: User
                The member to look for
        
        Returns
            Group
                The representation of user configuration file

        """
        return self.get_file(
            self.USER,
            str(user.id)
        )

    def user_from_id(self, user_id: int) -> Group:
        """Returns the given `discord.User.id` configuration file for self.cog.

        Parameters
            user_id: int
                The channel id to look for
        
        Returns
            Group
                The representation of user configuration file

        """
        return self.get_file(
            self.USER,
            str(user_id)
        )

    def member(self, member: Member) -> Group:
        """Returns the given `discord.Member` configuration file for self.cog.

        Parameters
            member: Member
                The member to look for
        
        Returns
            Group
                The representation of member configuration file

        """
        return self.get_file(
            self.MEMBER,
            str(member.guild.id),
            str(member.id)
        )

    def member_from_ids(self, guild_id: int, member_id: int) -> Group:
        """Returns the given `discord.Member` configuration file for self.cog.
        /!\ A `discord.Member` is a `discord.User` associated to a `discord.Guild`,
        so both IDs are needed.

        Parameters
            guild_id: int
                The guild id to look for
            member_id: int
                The user id to look for
        
        Returns
            Group
                The representation of member configuration file

        """
        return self.get_file(
            self.MEMBER,
            str(guild_id),
            str(member_id)
        )

    def clear(self, *scopes: str):
        pass

    def clear_all(self):
        self.clear()

    def clear_all_channels(self):
        self.clear(self.CHANNEL)

    def clear_all_globals(self):
        self.clear(self.GLOBAL)

    def clear_all_guilds(self):
        self.clear(self.GUILD)

    def clear_all_members(self, guild: Guild = None):
        if guild is not None:
            self.clear(self.MEMBER, str(guild.id))
        else:
            self.clear(self.MEMBER)

    def clear_all_roles(self):
        self.clear(self.ROLE)

    def clear_all_users(self):
        self.clear(self.USER)

############################################ FUNCTIONS ############################################

def mkdir_p(path: str):
    """Safely creates path to desired location if it doesn't exist.

    Parameters
        path: str
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
        write(path, if_error)
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
    data = Objectify.dictify(data)
    data = str_key_dict(data) if isinstance(data, dict) else data
    with safe_open(path, 'w') as file:
        file.write(json.dumps(data))