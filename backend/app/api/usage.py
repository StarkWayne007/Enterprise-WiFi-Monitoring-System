from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.dependencies import get_db
from app.services.usage import UsageService

router = APIRouter(prefix="/usage", tags=["Usage"])

usage_service = UsageService()


@router.get("/devices")
async def get_device_usage(
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    return await usage_service.get_device_usage(db)
