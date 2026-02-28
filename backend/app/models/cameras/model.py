from app.models.base import Base
from app.models.mixins import IdIntPk, TimestampMixin

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Enum as SAEnum, Boolean
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.user_events.model import UserEvents

class DirectionType(str, Enum):
    EXIT = "exit"
    ENTER = "enter"

class Cameras(Base, IdIntPk, TimestampMixin):
    
    __tablename__ = "cameras"
    
    device_ip: Mapped[str] = mapped_column(String(15), unique=True, nullable=False)
    username: Mapped[str] = mapped_column(String(50), nullable=False)
    password: Mapped[str] = mapped_column(String(50), nullable=False)
    direction: Mapped[DirectionType] = mapped_column(SAEnum(DirectionType), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    
    events: Mapped[list["UserEvents"]] = relationship("UserEvents", back_populates="camera")