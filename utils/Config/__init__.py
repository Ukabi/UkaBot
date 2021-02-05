############################################# IMPORTS #############################################
from discord import (
    Guild,
    Member,
    Role,
    User
)
from discord.abc import GuildChannel

##################### UTILS #####################
from typing import (
    Any,
    Dict,
    List,
    Union
)
from utils.Group import Group

############################################# CLASSES #############################################

class Config:
    GLOBAL = "global"
    GUILD = "guild"
    CHANNEL = "channel"
    ROLE = "role"
    USER = "user"
    MEMBER = "member"

    def __init__(self, cog: str = None, defaults: Union[List[Any], Dict[str, Any]] = {}):
        if not cog:
            raise NameError('Cog name must exist')
        else:
            self.cog = cog
            self.defaults = defaults

    def get_file(self, *primary_keys: str) -> Group:
        file = f'{self.cog}/'
        file += GLOBAL if not primary_keys else "/".join(primary_keys)
        file += ".json"
        return Group(file, defaults=self.defaults)

    def guild_from_id(self, guild_id: int) -> Group:
        return self.get_file(
            self.GUILD,
            str(guild_id)
        )

    def guild(self, guild: Guild) -> Group:
        return self.get_file(
            self.GUILD,
            str(guild.id)
        )

    def channel_from_id(self, channel_id: int) -> Group:
        return self.get_file(
            self.CHANNEL,
            str(channel_id)
        )

    def channel(self, channel: GuildChannel) -> Group:
        return self.get_file(
            self.CHANNEL,
            str(channel.id)
        )

    def role_from_id(self, role_id: int) -> Group:
        return self.get_file(
            self.ROLE,
            str(role_id)
        )

    def role(self, role: Role) -> Group:
        return self.get_file(
            self.ROLE,
            str(role.id)
        )

    def user_from_id(self, user_id: int) -> Group:
        return self.get_file(
            self.USER,
            str(user_id)
        )

    def user(self, user: User) -> Group:
        return self.get_file(
            self.USER,
            str(user.id)
        )

    def member_from_ids(self, guild_id: int, member_id: int) -> Group:
        return self.get_file(
            self.MEMBER,
            str(guild_id),
            str(member_id)
        )

    def member(self, member: Member) -> Group:
        return self.get_file(
            self.MEMBER,
            str(member.guild.id),
            str(member.id)
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