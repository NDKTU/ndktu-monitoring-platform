from app.models.base import Base
from app.models.mixins import IdIntPk

from datetime import datetime
from sqlalchemy import ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.users.model import User
    from app.models.cameras.model import Cameras


class UserEvents(Base, IdIntPk):
    
    __tablename__ = "user_events"
    
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    camera_id: Mapped[int] = mapped_column(ForeignKey("cameras.id"))
    enter_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    exit_time: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    
    user: Mapped["User"] = relationship("User", back_populates="events")
    camera: Mapped["Cameras"] = relationship("Cameras", back_populates="events")
     