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
from typing import Union

############################################ FUNCTIONS ############################################

def mkdir_p(path: str):
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise

def safe_open(
        path: str,
        mode: str,
        buffering: int,
        encoding: str,
        errors: str,
        newline: str,
        closefd: bool,
        opener: callable
    ):
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

def load(path: str, iferror: Union[list, dict] = []):
    try:
        with open(path, 'r') as file:
            return json.load(file)
    except FileNotFoundError or NotADirectoryError:
        with safe_open(path, 'w') as file:
            file.write(iferror)
        return iferror

def write(path, data: Union[list, dict]):
    with safe_open(path, 'w') as file:
        file.write(json.dumps(data))

############################################# CLASSES #############################################

class Objectify:
    def __init__(self, d: dict):
        for key, val in d.items():
            if isinstance(val, (list, tuple, set, frozenset)):
               setattr(
                   self,
                   key,
                   [Objectify(x) if isinstance(x, dict) else x for x in val]
                )

            else:
               setattr(
                   self,
                   key,
                   Objectify(val) if isinstance(val, dict) else val
                )

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
        if not scopes:
            # noinspection PyTypeChecker
            identifier_data = IdentifierData(self.cog_name, self.unique_identifier, "", (), (), 0)
            group = Group(identifier_data, defaults={}, driver=self.driver, config=self)
        else:
            cat, *scopes = scopes
            group = self._get_base_group(cat, *scopes)
        group.clear()

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