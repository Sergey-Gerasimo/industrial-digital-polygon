from infra.database.repositories import UserRepository
from infra.security import PasswordAuthenticationService, JWTHandler
from domain.entities.base.user import User, UserRole
from domain.values.Username import UserName


class AuthApplicationService:
    def __init__(
        self,
        user_repository: UserRepository,
        password_service: PasswordAuthenticationService,
        jwt_service: JWTHandler,
    ):
        self._user_reposytory = user_repository
        self._password_service = password_service
        self._jwt_service = jwt_service

    async def login(self, username: str, password: str) -> str:
        """Аутентифицирует пользователя и возвращает JWT токен с ролью.

        Args:
            username: Имя пользователя
            password: Пароль в открытом виде

        Returns:
            str: JWT access token, содержащий claim `role`

        Raises:
            ValueError: Если пользователь не найден или пароль неверный
        """
        user = await self._user_reposytory.get_by_username(UserName(username))
        if user is None:
            raise ValueError("Invalid credentials")

        if not self._password_service.verify_password(password, user.password_hash):
            raise ValueError("Invalid credentials")
        return self._jwt_service.create_access_token(
            user.id, extra_claims={"role": user.role.value}
        )

    async def register(self, username: str, password: str) -> str:
        """Регистрирует пользователя и возвращает JWT токен с ролью.

        Args:
            username: Имя пользователя
            password: Пароль в открытом виде

        Returns:
            str: JWT access token, содержащий claim `role`

        Raises:
            ValueError: Если пользователь с таким именем уже существует
        """
        user_name_vo = UserName(username)
        exists = await self._user_reposytory.exists_with_username(user_name_vo)
        if exists:
            raise ValueError("Username already taken")

        password_hash = self._password_service.hash_password(password)
        new_user = User(
            username=user_name_vo,
            password_hash=password_hash,
            role=UserRole.USER,
            is_active=True,
        )

        saved_user = await self._user_reposytory.save(new_user)
        return self._jwt_service.create_access_token(
            saved_user.id, extra_claims={"role": saved_user.role.value}
        )
