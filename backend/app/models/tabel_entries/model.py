from datetime import date as date_type
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import (
    Date,
    Enum as SAEnum,
    ForeignKey,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.mixins import IdIntPk, TimestampMixin

if TYPE_CHECKING:
    from app.models.employees.model import Employee


class TabelCode(str, Enum):
    B = "B"      # haqiqatda ishlangan kunlar
    A = "A"      # dam olish va bayram kunlari
    V = "V"      # ma'muriyat ruxsati bilan ishda qatnashmagan kunlar
    VU = "VU"    # kechalardagi ish vaqti
    N = "N"      # o'qish bo'yicha dam olishlar
    G = "G"      # o'quv ta'tili
    O = "O"      # bayramda ishlangan kunlar
    OU = "OU"    # davlat oldidagi majburiyatlar bajarish
    R = "R"      # mehnatga layoqatsizlik
    RP = "RP"    # keyingi va qo'shimcha mehnat ta'tili
    S = "S"      # tug'ish bilan bog'liq ta'tillar
    P = "P"      # navbatdan tashqari ish soatlari
    F = "F"      # progullar


class TabelEntry(Base, IdIntPk, TimestampMixin):

    __tablename__ = "tabel_entries"
    __table_args__ = (
        UniqueConstraint(
            "employee_id", "date", name="uq_tabel_entry_employee_date"
        ),
    )

    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id", ondelete="CASCADE"), nullable=False
    )
    date: Mapped[date_type] = mapped_column(Date, nullable=False)
    code: Mapped[TabelCode] = mapped_column(
        SAEnum(TabelCode, name="tabel_code"), nullable=False
    )
    comment: Mapped[str | None] = mapped_column(String(255), nullable=True)

    employee: Mapped["Employee"] = relationship("Employee")
