from pydantic import BaseModel, Field


class AuthenticateUserCommand(BaseModel):
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class RefreshTokensCommand(BaseModel):
    refresh_token: str = Field(..., min_length=1)


class GetCurrentUserQuery(BaseModel):
    access_token: str = Field(..., min_length=1)
