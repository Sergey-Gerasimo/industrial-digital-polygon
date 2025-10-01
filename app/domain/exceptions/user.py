from dataclasses import dataclass
from .base import AplicationException


@dataclass(frozen=True)
class UsernameAlreadyTaken(AplicationException):
    username: str
    message: str = "Username is already taken"


@dataclass(frozen=True)
class UserNotFound(AplicationException):
    user_id: str
    message: str = "User not found"


@dataclass(frozen=True)
class InvalidCredentials(AplicationException):
    message: str = "Invalid username or password"


@dataclass(frozen=True)
class UserNotActive(AplicationException):
    user_id: str
    message: str = "User account is not active"
