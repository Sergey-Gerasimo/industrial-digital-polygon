from enum import Enum


class PlayerRole(str, Enum):
    PRODUCTION = "production"
    PROCUREMENT = "procurement"
    COMMERCE = "commerce"
    ENGINEERING = "engineering"
