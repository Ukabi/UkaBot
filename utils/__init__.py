############################################# IMPORTS #############################################
from discord import (
    Guild,
    Member,
    Role,
    User
)
from discord.abc import GuildChannel

##################### UTILS #####################
import json
import os
import errno
from Objectify import Objectify
from typing import (
    Any,
    Dict,
    List,
    Union
)

############################################# CLASSES #############################################

class Group:
    def __init__(self, file: str, defaults: Union[list, dict] = {}):
        self.file = file
        self.data = load(self.file, iferror=defaults)

    def get(self):
        return self.data

    def set(self, data: Objectify):
        write(self.file, data)
        self.data = data

class Config(object):
    GLOBAL = "global"
    GUILD = "guild"
    CHANNEL = "channel"
    ROLE = "role"
    USER = "user"
    MEMBER = "member"

    def __init__(self, cog: str = None, defaults: dict = {}):
        if not cog:
            raise NameError('Cog name must exist')
        else:
            self.cog = cog
            self.defaults = defaults or {}

    def get_file(self, *primary_keys: str):
        primary_keys = (self.cog, *primary_keys)
        file = self.cog
        file += GLOBAL if not primary_keys else "/".join(primary_keys)
        file += ".json"
        return Group(file, defaults=self.defaults)

    def guild_from_id(self, guild_id: int):
        return self.get_file(self.GUILD, str(guild_id))

    def guild(self, guild: Guild):
        return self.get_file(self.GUILD, str(guild.id))

    def channel_from_id(self, channel_id: int):
        return self.get_file(self.CHANNEL, str(channel_id))

    def channel(self, channel: GuildChannel):
        return self.get_file(self.CHANNEL, str(channel.id))

    def role_from_id(self, role_id: int):
        return self.get_file(self.ROLE, str(role_id))

    def role(self, role: Role):
        return self.get_file(self.ROLE, str(role.id))

    def user_from_id(self, user_id: int):
        return self.get_file(self.USER, str(user_id))

    def user(self, user: User):
        return self.get_file(self.USER, str(user.id))

    def member_from_ids(self, guild_id: int, member_id: int):
        return self.get_file(self.MEMBER, str(guild_id), str(member_id))

    def member(self, member: Member):
        return self.get_file(self.MEMBER, str(member.guild.id), str(member.id))

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
            return
        self.clear(self.MEMBER)

    def clear_all_roles(self):
        self.clear(self.ROLE)

    def clear_all_users(self):
        self.clear(self.USER)

############################################ FUNCTIONS ############################################

def mkdir_p(path: str):
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise OSError("Couldn't create file or directory.")

def safe_open(
        path: str,
        mode: str,
        buffering: int,
        encoding: str,
        errors: str,
        newline: str,
        closefd: bool,
        opener: callable
    ) -> open:
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

def load(
        path: str,
        iferror: Union[list, dict] = [],
        toobject: bool = False
    ) -> Union[list, dict, Objectify]:
    try:
        with open(path, 'r') as file:
            data = json.load(file)
    except FileNotFoundError or NotADirectoryError:
        with safe_open(path, 'w') as file:
            file.write(iferror)
        data = iferror
    return Objectify.objectify(data) if toobject else data

def write(path, data: Union[List[Objectify], Objectify, List[Any], Dict[str, Any]]):
    with safe_open(path, 'w') as file:
        file.write(json.dumps(Objectify.dictify(data)))