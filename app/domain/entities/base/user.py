from dataclasses import dataclass, field
from typing import Optional
from uuid import UUID, uuid4
import uuid
from datetime import datetime, timezone

from infra.database.models import created_at

from ...values import HashedPasswordSHA256, UserName
from ...enums import UserRole, PlayerRole


@dataclass
class User:
    username: UserName
    password_hash: HashedPasswordSHA256
    role: UserRole
    is_active: bool
    id: Optional[UUID] = None
    updated_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    @classmethod
    def create(
        cls,
        username: UserName,
        password_hash: HashedPasswordSHA256,
        role: UserRole = UserRole.USER,
    ) -> "User":
        """Factory method for creating new users"""
        now = datetime.now(timezone.utc)
        return cls(
            id=uuid4(),
            username=username,
            password_hash=password_hash,
            role=role,
            is_active=True,
            created_at=now,
            updated_at=now,
        )

    def change_username(self, new_username: UserName) -> None:
        """Business operation for changing username"""
        self.username = new_username

    def change_password(self, new_password_hash: HashedPasswordSHA256) -> None:
        """Business operation for changing password"""
        self.password_hash = new_password_hash

    def change_role(self, new_role: UserRole) -> None:
        """Business operation for changing role"""
        self.role = new_role

    def activate(self) -> None:
        """Business operation for activating user"""
        self.is_active = True

    def deactivate(self) -> None:
        """Business operation for deactivating user"""
        self.is_active = False

    def authenticate(self, password_hash: HashedPasswordSHA256) -> bool:
        """Business operation for authentication"""
        return self.password_hash == password_hash and self.is_active


@dataclass()
class Player:
    user_id: str
    role: PlayerRole
    player_id: str = field(default_factory=lambda: str(uuid4()))
