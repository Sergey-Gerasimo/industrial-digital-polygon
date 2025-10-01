from fastapi import APIRouter, Depends, HTTPException, status, Response
from uuid import UUID
from logging import Logger

from infra.config.log_settings import app_logger
from application.services import AuthApplicationService, UserApplicationService

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
from ..dependencies import (
    get_auth_service,
    get_user_service,
    get_current_user,
    get_logger,
)


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED
)
async def register(
    request: RegisterRequest,
    user_service: UserApplicationService = Depends(get_user_service),
    auth_service: AuthApplicationService = Depends(get_auth_service),
    logger: Logger = Depends(get_logger),
):
    """User registration - always creates USER role"""
    try:
        logger.debug(
            f"Creating user in DB with {request.username=} and role={UserRole.USER}"
        )
        # Создаем пользователя с ролью USER по умолчанию
        user = await user_service.create(
            username=request.username,
            password=request.password,
            role=UserRole.USER,  # Всегда USER при регистрации
        )

        logger.debug(f"User {user.username=} created successfylly with {user.id=}")

        # Генерируем токены для нового пользователя
        logger.debug(f"Creating JWT tokens for {user.username=}")
        access_token = auth_service._jwt_service.create_access_token(
            subject=str(user.id),
            expires_delta=settings.secrurity.access_token_expire_minutes,
        )
        refresh_token = auth_service._jwt_service.create_refresh_token(
            subject=str(user.id),
            expires_delta=settings.secrurity.refresh_token_expire_minutes,
        )

        logger.info(
            f"User {user.username} created succsessfully with ID: {str(user.id)}"
        )
        return AuthResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user=UserResponse.from_entity(user),
            message="User registered successfully",
            expires_in=settings.secrurity.access_token_expire_minutes,
            refresh_expire_in=settings.secrurity.refresh_token_expire_minutes,
        )

    except UsernameAlreadyTaken:
        logger.error(f"Registration conflict: username already exist")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Username already taken"
        )
    except Exception as e:
        logger.error(f"Internal server error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}",
        )


@router.post("/login", response_model=AuthResponse)
async def login(
    credentials: LoginRequest,
    auth_service: AuthApplicationService = Depends(get_auth_service),
    logger: Logger = Depends(get_logger),
):
    """User login"""
    try:
        logger.debug(f"Attempting login for {credentials.username=}")
        user, access_token, refresh_token = await auth_service.authenticate_user(
            username=credentials.username,
            password=credentials.password,
            access_expire_in=settings.secrurity.access_token_expire_minutes,
            refresh_expire_in=settings.secrurity.refresh_token_expire_minutes,
        )

        logger.debug(f"Authentication successful for {user.username=} with {user.id=}")
        logger.debug(f"JWT tokens generated for {user.username=} JWT: {access_token}")
        logger.info(f"User {user.username} logged in successfully")

        return AuthResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user=UserResponse.from_entity(user),
            message="Login successful",
            expires_in=settings.secrurity.access_token_expire_minutes,
            refresh_expire_in=settings.secrurity.refresh_token_expire_minutes,
        )
    except InvalidCredentials:
        logger.error(f"Invalid credentials for {credentials.username=}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )
    except UserNotActive:
        logger.error(f"Login attempt for inactive user {credentials.username=}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="User account is not active"
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: RefreshRequest,
    auth_service: AuthApplicationService = Depends(get_auth_service),
    logger: Logger = Depends(get_logger),
):
    """Refresh access token"""
    try:
        logger.debug(f"Attempting token refresh with provided refresh token")

        access_token, refresh_token = await auth_service.refresh_tokens(
            refresh_token=request.refresh_token,
            access_expire_in=settings.secrurity.access_token_expire_minutes,
            refresh_expire_in=settings.secrurity.refresh_token_expire_minutes,
        )
        logger.debug(f"New tokens generated successfully")
        logger.info(f"Token refresh completed successfully")

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            message="Token refreshed successfully",
            expires_in=settings.secrurity.access_token_expire_minutes,
            refresh_expire_in=settings.secrurity.refresh_token_expire_minutes,
        )
    except InvalidCredentials:
        logger.error(f"Invalid or expired refresh token provided")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )


@router.post("/logout", response_model=LogoutResponse)
async def logout(
    response: Response,
    current_user: UserResponse = Depends(get_current_user),
    logger: Logger = Depends(get_logger),
):
    """User logout"""
    try:
        logger.debug(
            f"Starting logout process for {current_user.username=} with {current_user.id=}"
        )
        # In a real app, you might want to blacklist the token
        # For now, we just clear cookies if using them
        response.delete_cookie("access_token")
        response.delete_cookie("refresh_token")

        logger.debug(f"Cookies cleared for {current_user.username=}")
        logger.info(f"User {current_user.username} logged out successfully")

        return LogoutResponse(message="Successfully logged out")

    except Exception as e:
        logger.error(f"Logout error for {current_user.username=}: {e}")
        # нам плевать удалось ли нам очистить куки или нет.
        return LogoutResponse(message="Successfully logged out")


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: UserResponse = Depends(get_current_user),
    logger: Logger = Depends(get_logger),
):
    logger.debug(
        f"Fetching current user info for {current_user.username=} with {current_user.id=}"
    )
    logger.info(f"User info retrieved for {current_user.username}")

    return UserResponse.from_entity(current_user)


@router.post("/verify-token", response_model=SuccessResponse)
async def verify_token(
    current_user: UserResponse = Depends(get_current_user),
    logger: Logger = Depends(get_logger),
):
    logger.debug(
        f"Token verification for {current_user.username=} with {current_user.id=}"
    )
    logger.info(f"Token verified successfully for {current_user.username}")
    return SuccessResponse(message="Token is valid")


@router.post("/change-password", response_model=SuccessResponse)
async def change_password(
    password_data: ChangePasswordRequest,
    user_service: UserApplicationService = Depends(get_user_service),
    current_user: UserResponse = Depends(get_current_user),
    logger: Logger = Depends(get_logger),
):
    """Change current user password"""
    try:
        logger.debug(
            f"Starting password change for {current_user.username=} with {current_user.id=}"
        )

        await user_service.update(
            user_id=current_user.id, password=password_data.new_password
        )

        logger.debug(f"Password updated successfully for {current_user.username=}")
        logger.info(f"Password changed successfully for {current_user.username}")

        return SuccessResponse(message="Password changed successfully")
    except UserNotFound:
        logger.error(f"User not found during password change: {current_user.id=}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
