from app.models.base import Base
from app.models.mixins import IdIntPk, TimestampMixin

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Boolean
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.user_events.model import UserEvents

class User(Base, IdIntPk, TimestampMixin):
    
    __tablename__ = "users"
    
    username: Mapped[str] = mapped_column(String(50), nullable=False)
    password: Mapped[str | None] = mapped_column(String(50), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    in_work: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    
    events: Mapped[list["UserEvents"]] = relationship("UserEvents", back_populates="user")