from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from uuid import UUID

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
from ..dependencies import get_user_service, require_admin, get_current_user

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    command: CreateUserCommand,
    user_service: UserApplicationService = Depends(require_admin),
):
    """Register new user"""
    try:
        user = await user_service.create_user(
            username=command.username,
            password=command.password,
            role=command.role,
        )
        return UserResponse.from_entity(user)
    except UsernameAlreadyTaken:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Username already taken"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: UserResponse = Depends(get_current_user),
):
    """Get current user profile"""
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_current_user_profile(
    update_data: UserUpdate,
    user_service: UserApplicationService = Depends(get_user_service),
    current_user: UserResponse = Depends(get_current_user),
):
    """Update current user profile"""
    try:
        if update_data.username and update_data.username != current_user.username:
            user = await user_service.update_user_username(
                user_id=current_user.id, new_username=update_data.username
            )
            return UserResponse.from_entity(user)

        return current_user
    except UsernameAlreadyTaken:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Username already taken"
        )
    except UserNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )


@router.post("/me/change-password", response_model=SuccessResponse)
async def change_current_user_password(
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


# Admin endpoints
@router.get("/", response_model=UserListResponse, dependencies=[Depends(require_admin)])
async def get_users_list(
    user_service: UserApplicationService = Depends(get_user_service),
    is_active: Optional[bool] = Query(None),
    role: Optional[UserRole] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """Get users list (admin only)"""
    try:
        users = await user_service.list_users(limit=limit, offset=offset)

        # Filtering (in real app this would be in repository)
        if is_active is not None:
            users = [user for user in users if user.is_active == is_active]
        if role is not None:
            users = [user for user in users if user.role == role]

        user_responses = [UserResponse.from_entity(user) for user in users]
        return UserListResponse(
            users=user_responses,
            total=len(user_responses),
            page=offset // limit + 1,
            size=limit,
        )
    except Exception as e:
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
):
    """Get user by ID (admin only)"""
    try:
        user = await user_service.get_user_by_id(user_id)
        return UserResponse.from_entity(user)
    except UserNotFound:
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
):
    """Update user username (admin only)"""
    try:
        user = await user_service.update_user_username(
            user_id=user_id, new_username=command.new_username
        )
        return UserResponse.from_entity(user)
    except UsernameAlreadyTaken:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Username already taken"
        )
    except UserNotFound:
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
):
    """Update user password (admin only)"""
    try:
        await user_service.update_user_password(
            user_id=user_id, new_password=command.new_password
        )
        return SuccessResponse(message="User password updated successfully")
    except UserNotFound:
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
):
    """Update user role (admin only)"""
    try:
        user = await user_service.update_user_role(
            user_id=user_id, new_role=command.new_role
        )
        return UserResponse.from_entity(user)
    except UserNotFound:
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
):
    """Deactivate user (admin only)"""
    try:
        user = await user_service.deactivate_user(user_id)
        return UserResponse.from_entity(user)
    except UserNotFound:
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
):
    """Activate user (admin only)"""
    try:
        user = await user_service.activate_user(user_id)
        return UserResponse.from_entity(user)
    except UserNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )


@router.delete(
    "/{user_id}", response_model=SuccessResponse, dependencies=[Depends(require_admin)]
)
async def delete_user(
    user_id: UUID,
    user_service: UserApplicationService = Depends(get_user_service),
):
    """Delete user (admin only)"""
    try:
        success = await user_service.delete_user(user_id)
        if success:
            return SuccessResponse(message="User deleted successfully")
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )
    except UserNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
