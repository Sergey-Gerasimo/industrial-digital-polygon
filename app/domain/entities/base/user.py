from dataclasses import dataclass, field
from enum import Enum
import uuid

from domain.values.Username import UserName
from domain.values.hashed_password import HashedPasswordSHA256


@dataclass(frozen=True)
class User:
    id: str
    username: UserName
    password_hash: HashedPasswordSHA256
    is_active: bool


class PlayerRole(Enum, str):
    PRODUCTION = "production"
    PROCUREMENT = "procurement"
    COMMERCE = "commerce"
    ENGINEERING = "engineering"


@dataclass(frozen=True)
class Player:
    player_id: str = field(default_factory=lambda: str(uuid()))
    user_id: str
    role: PlayerRole
