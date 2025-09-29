from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID as PyUUID, uuid4
from sqlalchemy import String, event
from sqlalchemy.dialects.postgresql import UUID as SAUUID
from sqlalchemy.orm import Mapped, mapped_column
from infra.database import Base


get_current_time = lambda: datetime.now(timezone.utc).replace(tzinfo=None)

idpk = Annotated[int, mapped_column(primary_key=True)]
UUID_PK = Annotated[
    PyUUID,
    mapped_column(SAUUID(as_uuid=True), default=uuid4, primary_key=True),
]
created_at = Annotated[datetime, mapped_column(default=get_current_time)]


class User(Base):
    __tablename__ = "users"

    id: Mapped[UUID_PK]
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=get_current_time)
    updated_at: Mapped[datetime] = mapped_column(
        default=get_current_time, onupdate=get_current_time
    )
    is_active: Mapped[bool] = mapped_column(default=True)


@event.listens_for(User, "before_insert")
def set_created_date(mapper, connection, target):
    target.created_at = get_current_time()
    target.updated_at = get_current_time()


@event.listens_for(User, "before_update")
def set_updated_date(mapper, connection, target):
    target.updated_at = get_current_time()
