from fastapi import APIRouter, Depends, HTTPException, status

from application.api.dto.auth_dto import (
    RegisterUserRequest,
    RegisterUserResponse,
    LoginRequest,
    LoginResponse,
    RefreshTokenRequest,
    RefreshTokenResponse,
)
from application.api.dependencies.auth import get_auth_service
from application.services import AuthApplicationService
from infra.security.jwt_handler import JWTError


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=RegisterUserResponse)
async def register(
    payload: RegisterUserRequest,
    auth_service: AuthApplicationService = Depends(get_auth_service),
):
    try:
        token = await auth_service.register(payload.username, payload.password)
        return {
            "access_token": token,
            "token_type": "Bearer",
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/login", response_model=LoginResponse)
async def login(
    payload: LoginRequest,
    auth_service: AuthApplicationService = Depends(get_auth_service),
):
    try:
        token = await auth_service.login(payload.username, payload.password)
        return {
            "access_token": token,
            "token_type": "Bearer",
        }
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )


@router.post("/refresh", response_model=RefreshTokenResponse)
async def refresh(
    payload: RefreshTokenRequest,
    auth_service: AuthApplicationService = Depends(get_auth_service),
):
    # Проверяем refresh токен и выдаём новый access токен с той же ролью
    payload_data = auth_service._jwt_service.verify_token(payload.refresh_token)
    if not payload_data or "sub" not in payload_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )

    user_id = payload_data["sub"]
    role = payload_data.get("role")
    token = auth_service._jwt_service.create_access_token(
        user_id, extra_claims={"role": role} if role else None
    )
    return {
        "access_token": token,
        "token_type": "Bearer",
    }
