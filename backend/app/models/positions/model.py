from app.models.base import Base
from app.models.mixins import IdIntPk, TimestampMixin
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.employees.model import Employee


class Position(Base, IdIntPk, TimestampMixin):
    __tablename__ = "positions"

    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)

    employees: Mapped[list["Employee"]] = relationship(
        "Employee", back_populates="position"
    )
