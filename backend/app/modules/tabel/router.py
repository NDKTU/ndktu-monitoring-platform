from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db_helper import db_helper
from app.modules.tabel.repository import TabelRepository
from app.modules.tabel.service import TabelService
from app.modules.tabel.schemas import (
    TabelEntryDeleteRequest,
    TabelEntryResult,
    TabelEntryUpsertRequest,
    TabelMonthRequest,
    TabelMonthResponse,
)

router = APIRouter(
    tags=["Tabel"],
    prefix="/tabel",
)


def get_tabel_service(
    session: AsyncSession = Depends(db_helper.session_getter),
) -> TabelService:
    repository = TabelRepository(session)
    return TabelService(repository)


@router.get("/month", response_model=TabelMonthResponse)
async def get_month(
    request: TabelMonthRequest = Depends(),
    service: TabelService = Depends(get_tabel_service),
):
    return await service.get_month(request)


@router.put("/entry", response_model=TabelEntryResult)
async def upsert_entry(
    payload: TabelEntryUpsertRequest,
    service: TabelService = Depends(get_tabel_service),
):
    return await service.upsert_entry(payload)


@router.delete("/entry", response_model=TabelEntryResult)
async def delete_entry(
    payload: TabelEntryDeleteRequest,
    service: TabelService = Depends(get_tabel_service),
):
    return await service.delete_entry(payload)
