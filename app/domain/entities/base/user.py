from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import uuid

from domain.values.Username import UserName
from domain.values.hashed_password import HashedPasswordSHA256


@dataclass()
class User:
    username: UserName
    password_hash: HashedPasswordSHA256
    role: "UserRole" = None
    is_active: bool = True
    id: Optional[str] = None


class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"


class PlayerRole(str, Enum):
    PRODUCTION = "production"
    PROCUREMENT = "procurement"
    COMMERCE = "commerce"
    ENGINEERING = "engineering"


@dataclass()
class Player:
    user_id: str
    role: PlayerRole
    player_id: str = field(default_factory=lambda: str(uuid.uuid4()))
