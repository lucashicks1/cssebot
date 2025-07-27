"""Utils for teams and roles."""

from discord import Guild, Member, Role

TEAM_PREFIX = "Team "


def _is_team_role(role: Role) -> bool:
    """Check if a role is a team role."""
    return role.name.startswith(TEAM_PREFIX)


def get_team_roles(guild: Guild) -> list[Role]:
    """Get all team roles in a guild."""
    return [role for role in guild.roles if _is_team_role(role)]


def get_member_team(member: Member) -> Role | None:
    """Return the team role the member has."""
    return next((role for role in member.roles if _is_team_role(role)), None)


def is_in_team(member: Member) -> bool:
    """Check whether a member is in any team."""
    return get_member_team(member) is not None
