from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from uuid import UUID
from logging import Logger

from application.services import UserApplicationService
from application.dto.user_commands import (
    CreateUserCommand,
    UpdateUserUsernameCommand,
    UpdateUserPasswordCommand,
    UpdateUserRoleCommand,
    ChangeUserStatusCommand,
)
from application.api.dto import (
    UserResponse,
    UserListResponse,
    UserUpdate,
    SuccessResponse,
    ChangePasswordRequest,
)
from domain.exceptions.user import UsernameAlreadyTaken, UserNotFound
from domain.enums import UserRole
from ..dependencies import get_user_service, require_admin, get_current_user, get_logger

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: UserResponse = Depends(get_current_user),
    logger: Logger = Depends(get_logger),
):
    """Get current user profile"""
    logger.debug(
        f"Fetching profile for {current_user.username=} with {current_user.id=}"
    )
    logger.info(f"Profile retrieved for {current_user.username}")

    return current_user


@router.put("/me", response_model=UserResponse)
async def update_current_user_profile(
    update_data: UserUpdate,
    user_service: UserApplicationService = Depends(get_user_service),
    current_user: UserResponse = Depends(get_current_user),
    logger: Logger = Depends(get_logger),
):
    """Update current user profile"""
    try:
        logger.debug(
            f"Starting profile update for {current_user.username=} with {update_data=}"
        )

        if update_data.username and update_data.username != current_user.username:
            logger.debug(
                f"Updating username from {current_user.username} to {update_data.username}"
            )

            user = await user_service.update_user_username(
                user_id=current_user.id, new_username=update_data.username
            )

            logger.debug(f"Username updated successfully to {user.username=}")
            logger.info(
                f"User {current_user.username} updated username to {user.username}"
            )

            return UserResponse.from_entity(user)

        logger.debug(f"No changes detected for {current_user.username=}")
        logger.info(
            f"Profile update completed with no changes for {current_user.username}"
        )

        return current_user

    except UsernameAlreadyTaken:
        logger.error(f"Username already taken: {update_data.username=}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Username already taken"
        )
    except UserNotFound:
        logger.error(f"User not found during profile update: {current_user.id=}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )


@router.post("/me/change-password", response_model=SuccessResponse)
async def change_current_user_password(
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

        await user_service.update_user_password(
            user_id=current_user.id, new_password=password_data.new_password
        )

        logger.debug(f"Password updated successfully for {current_user.username=}")
        logger.info(f"Password changed successfully for {current_user.username}")

        return SuccessResponse(message="Password changed successfully")

    except UserNotFound:
        logger.error(f"User not found during password change: {current_user.id=}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )


# Admin endpoints
@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    command: CreateUserCommand,
    user_service: UserApplicationService = Depends(require_admin),
    logger: Logger = Depends(get_logger),
):
    """Register new user"""
    try:
        logger.debug(
            f"Admin creating user with {command.username=} and {command.role=}"
        )
        user = await user_service.create_user(
            username=command.username,
            password=command.password,
            role=command.role,
        )

        logger.debug(f"User {user.username=} created successfully with {user.id=}")
        logger.info(f"Admin created user {user.username} with role {user.role}")

        return UserResponse.from_entity(user)

    except UsernameAlreadyTaken:
        logger.error(f"Username already taken: {command.username=}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Username already taken"
        )


@router.get("/", response_model=UserListResponse, dependencies=[Depends(require_admin)])
async def get_users_list(
    user_service: UserApplicationService = Depends(get_user_service),
    is_active: Optional[bool] = Query(None),
    role: Optional[UserRole] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    logger: Logger = Depends(get_logger),
):
    """Get users list (admin only)"""
    try:
        logger.debug(
            f"Admin fetching users list with {is_active=} {role=} {limit=} {offset=}"
        )

        users = await user_service.list_users(limit=limit, offset=offset)

        # Filtering (in real app this would be in repository)
        if is_active is not None:
            users = [user for user in users if user.is_active == is_active]
        if role is not None:
            users = [user for user in users if user.role == role]

        user_responses = [UserResponse.from_entity(user) for user in users]

        logger.debug(f"Retrieved {len(user_responses)} users with applied filters")
        logger.info(f"Admin retrieved users list with {len(user_responses)} users")

        return UserListResponse(
            users=user_responses,
            total=len(user_responses),
            page=offset // limit + 1,
            size=limit,
        )
    except Exception as e:
        logger.error(f"Error retrieving users list: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving users list",
        )


@router.get(
    "/{user_id}", response_model=UserResponse, dependencies=[Depends(require_admin)]
)
async def get_user_by_id(
    user_id: UUID,
    user_service: UserApplicationService = Depends(get_user_service),
    logger: Logger = Depends(get_logger),
):
    """Get user by ID (admin only)"""
    try:
        logger.debug(f"Admin fetching user by ID: {user_id=}")

        user = await user_service.get_user_by_id(user_id)

        logger.debug(f"User found: {user.username=} with {user.id=}")
        logger.info(f"Admin retrieved user {user.username} by ID")

        return UserResponse.from_entity(user)

    except UserNotFound:
        logger.error(f"User not found with ID: {user_id=}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )


@router.put(
    "/{user_id}/username",
    response_model=UserResponse,
    dependencies=[Depends(require_admin)],
)
async def update_user_username(
    user_id: UUID,
    command: UpdateUserUsernameCommand,
    user_service: UserApplicationService = Depends(get_user_service),
    logger: Logger = Depends(get_logger),
):
    """Update user username (admin only)"""
    try:
        logger.debug(
            f"Admin updating username for {user_id=} to {command.new_username=}"
        )

        user = await user_service.update_user_username(
            user_id=user_id, new_username=command.new_username
        )

        logger.debug(f"Username updated successfully to {user.username=}")
        logger.info(f"Admin updated username to {user.username} for user ID {user_id}")

        return UserResponse.from_entity(user)

    except UsernameAlreadyTaken:
        logger.error(f"Username already taken: {command.new_username=}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Username already taken"
        )
    except UserNotFound:
        logger.error(f"User not found: {user_id=}")

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )


@router.put(
    "/{user_id}/password",
    response_model=SuccessResponse,
    dependencies=[Depends(require_admin)],
)
async def update_user_password(
    user_id: UUID,
    command: UpdateUserPasswordCommand,
    user_service: UserApplicationService = Depends(get_user_service),
    logger: Logger = Depends(get_logger),
):
    """Update user password (admin only)"""
    try:
        logger.debug(f"Admin updating password for {user_id=}")

        await user_service.update_user_password(
            user_id=user_id, new_password=command.new_password
        )

        logger.debug(f"Password updated successfully for {user_id=}")
        logger.info(f"Admin updated password for user ID {user_id}")

        return SuccessResponse(message="User password updated successfully")

    except UserNotFound:
        logger.error(f"User not found: {user_id=}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )


@router.put(
    "/{user_id}/role",
    response_model=UserResponse,
    dependencies=[Depends(require_admin)],
)
async def update_user_role(
    user_id: UUID,
    command: UpdateUserRoleCommand,
    user_service: UserApplicationService = Depends(get_user_service),
    logger: Logger = Depends(get_logger),
):
    """Update user role (admin only)"""
    try:
        logger.debug(f"Admin updating role for {user_id=} to {command.new_role=}")

        user = await user_service.update_user_role(
            user_id=user_id, new_role=command.new_role
        )

        logger.debug(f"Role updated successfully to {user.role=}")
        logger.info(f"Admin updated role to {user.role} for user ID {user_id}")

        return UserResponse.from_entity(user)

    except UserNotFound:
        logger.error(f"User not found: {user_id=}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )


@router.post(
    "/{user_id}/deactivate",
    response_model=UserResponse,
    dependencies=[Depends(require_admin)],
)
async def deactivate_user(
    user_id: UUID,
    user_service: UserApplicationService = Depends(get_user_service),
    logger: Logger = Depends(get_logger),
):
    """Deactivate user (admin only)"""
    try:
        logger.debug(f"Admin deactivating user: {user_id=}")

        user = await user_service.deactivate_user(user_id)

        logger.debug(
            f"User deactivated successfully: {user.username=} with {user.is_active=}"
        )
        logger.info(f"Admin deactivated user {user.username} with ID {user_id}")

        return UserResponse.from_entity(user)

    except UserNotFound:
        logger.error(f"User not found: {user_id=}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )


@router.post(
    "/{user_id}/activate",
    response_model=UserResponse,
    dependencies=[Depends(require_admin)],
)
async def activate_user(
    user_id: UUID,
    user_service: UserApplicationService = Depends(get_user_service),
    logger: Logger = Depends(get_logger),
):
    """Activate user (admin only)"""
    try:
        logger.debug(f"Admin activating user: {user_id=}")

        user = await user_service.activate_user(user_id)

        logger.debug(
            f"User activated successfully: {user.username=} with {user.is_active=}"
        )
        logger.info(f"Admin activated user {user.username} with ID {user_id}")

        return UserResponse.from_entity(user)

    except UserNotFound:
        logger.error(f"User not found: {user_id=}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )


@router.delete(
    "/{user_id}", response_model=SuccessResponse, dependencies=[Depends(require_admin)]
)
async def delete_user(
    user_id: UUID,
    user_service: UserApplicationService = Depends(get_user_service),
    logger: Logger = Depends(get_logger),
):
    """Delete user (admin only)"""
    try:
        logger.debug(f"Admin deleting user: {user_id=}")

        success = await user_service.delete_user(user_id)

        if success:
            logger.debug(f"User deleted successfully: {user_id=}")
            logger.info(f"Admin deleted user with ID {user_id}")
            return SuccessResponse(message="User deleted successfully")
        else:
            logger.error(f"User deletion failed: {user_id=}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

    except UserNotFound:
        logger.error(f"User not found: {user_id=}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
