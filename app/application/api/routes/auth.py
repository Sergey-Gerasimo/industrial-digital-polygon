import secrets
from weakref import ref
from fastapi import APIRouter, Depends, HTTPException, security, status, Response
from uuid import UUID

from infra.config.log_settings import app_logger
from application.services import AuthApplicationService, UserApplicationService
from application.dto.auth_commands import (
    AuthenticateUserCommand,
    RefreshTokensCommand,
)

from infra.config import settings
from application.api.dto import (
    ChangePasswordRequest,
    LoginRequest,
    RefreshRequest,
    AuthResponse,
    TokenResponse,
    LogoutResponse,
    SuccessResponse,
    UserRole,
    UserResponse,
    RegisterRequest,
)
from domain.exceptions.user import (
    InvalidCredentials,
    UserNotActive,
    UserNotFound,
    UsernameAlreadyTaken,
)
from ..dependencies import get_auth_service, get_user_service, get_current_user


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED
)
async def register(
    request: RegisterRequest,
    user_service: UserApplicationService = Depends(get_user_service),
    auth_service: AuthApplicationService = Depends(get_auth_service),
):
    """User registration - always creates USER role"""
    try:
        # Создаем пользователя с ролью USER по умолчанию
        user = await user_service.create(
            username=request.username,
            password=request.password,
            role=UserRole.USER,  # Всегда USER при регистрации
        )

        # Генерируем токены для нового пользователя
        access_token = auth_service._jwt_service.create_access_token(
            subject=str(user.id),
            expires_delta=settings.secrurity.access_token_expire_minutes,
        )
        refresh_token = auth_service._jwt_service.create_refresh_token(
            subject=str(user.id),
            expires_delta=settings.secrurity.refresh_token_expire_minutes,
        )
        app_logger.debug(user)

        return AuthResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user=UserResponse.from_entity(user),
            message="User registered successfully",
            expires_in=settings.secrurity.access_token_expire_minutes,
            refresh_expire_in=settings.secrurity.refresh_token_expire_minutes,
        )

    except UsernameAlreadyTaken:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Username already taken"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}",
        )


@router.post("/login", response_model=AuthResponse)
async def login(
    credentials: LoginRequest,
    auth_service: AuthApplicationService = Depends(get_auth_service),
):
    """User login"""
    try:
        user, access_token, refresh_token = await auth_service.authenticate_user(
            username=credentials.username,
            password=credentials.password,
            access_expire_in=settings.secrurity.access_token_expire_minutes,
            refresh_expire_in=settings.secrurity.refresh_token_expire_minutes,
        )

        return AuthResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user=UserResponse.from_entity(user),
            message="Login successful",
            access_expire_in=settings.secrurity.access_token_expire_minutes,
            refresh_expire_in=settings.secrurity.refresh_token_expire_minutes,
        )
    except InvalidCredentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )
    except UserNotActive:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="User account is not active"
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: RefreshRequest,
    auth_service: AuthApplicationService = Depends(get_auth_service),
):
    """Refresh access token"""
    try:
        access_token, refresh_token = await auth_service.refresh_tokens(
            refresh_token=request.refresh_token,
            access_expire_in=settings.secrurity.access_token_expire_minutes,
            refresh_expire_in=settings.secrurity.refresh_token_expire_minutes,
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            message="Token refreshed successfully",
            access_expire_in=settings.secrurity.access_token_expire_minutes,
            refresh_expire_in=settings.secrurity.refresh_token_expire_minutes,
        )
    except InvalidCredentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )


@router.post("/logout", response_model=LogoutResponse)
async def logout(
    response: Response,
    current_user: UserResponse = Depends(get_current_user),
):
    """User logout"""
    # In a real app, you might want to blacklist the token
    # For now, we just clear cookies if using them
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")

    return LogoutResponse(message="Successfully logged out")


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: UserResponse = Depends(get_current_user),
):
    """Get current user information"""
    return current_user


@router.post("/verify-token", response_model=SuccessResponse)
async def verify_token(
    current_user: UserResponse = Depends(get_current_user),
):
    """Verify access token validity"""
    return SuccessResponse(message="Token is valid")


@router.post("/change-password", response_model=SuccessResponse)
async def change_password(
    password_data: ChangePasswordRequest,
    user_service: UserApplicationService = Depends(get_user_service),
    current_user: UserResponse = Depends(get_current_user),
):
    """Change current user password"""
    try:
        await user_service.update_user_password(
            user_id=current_user.id, new_password=password_data.new_password
        )
        return SuccessResponse(message="Password changed successfully")
    except UserNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
