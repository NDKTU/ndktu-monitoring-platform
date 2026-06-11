from typing import TYPE_CHECKING
from app.models.base import Base
from app.models.mixins import IdIntPk, TimestampMixin

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Boolean, ForeignKey, Integer

if TYPE_CHECKING:
    from app.models.rbac.model import Role


class User(Base, IdIntPk, TimestampMixin):

    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    
    role_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("roles.id", ondelete="SET NULL"), nullable=True
    )

    role: Mapped["Role | None"] = relationship(
        "Role", back_populates="users"
    )
