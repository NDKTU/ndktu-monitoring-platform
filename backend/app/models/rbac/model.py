from typing import TYPE_CHECKING
from app.models.base import Base
from app.models.mixins import IdIntPk, TimestampMixin

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, ForeignKey

if TYPE_CHECKING:
    from app.models.users.model import User

class RolePermission(Base):
    __tablename__ = "role_permissions"

    role_id: Mapped[int] = mapped_column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True)
    permission_id: Mapped[int] = mapped_column(Integer, ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True)


class Role(Base, IdIntPk, TimestampMixin):
    __tablename__ = "roles"

    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    users: Mapped[list["User"]] = relationship(
        "User", back_populates="role"
    )
    permissions: Mapped[list["Permission"]] = relationship(
        "Permission", secondary="role_permissions", back_populates="roles"
    )


class Permission(Base, IdIntPk, TimestampMixin):
    __tablename__ = "permissions"

    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    roles: Mapped[list["Role"]] = relationship(
        "Role", secondary="role_permissions", back_populates="permissions"
    )
