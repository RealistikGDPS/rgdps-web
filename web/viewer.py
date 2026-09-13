from dataclasses import dataclass

from poltergeist_core.resources import Permission
from poltergeist_core.resources import User
from poltergeist_core.utilities import permissions


@dataclass(frozen=True, slots=True)
class Viewer:
    """Who is looking at the page and what they are allowed to do."""

    user: User
    grants: frozenset[str]

    @property
    def id(self) -> int:
        return self.user.id

    @property
    def username(self) -> str:
        return self.user.username

    @property
    def is_operator(self) -> bool:
        return self.may(Permission.ADMIN_ACCESS)

    def may(self, permission: str) -> bool:
        return permissions.is_granted(self.grants, permission)
