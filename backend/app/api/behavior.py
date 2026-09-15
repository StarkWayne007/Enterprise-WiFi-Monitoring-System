from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.dependencies import get_db
from app.services.behavior import BehaviorService

router = APIRouter(prefix="/behavior", tags=["Behavior"])

behavior_service = BehaviorService()


@router.get("/devices")
async def get_device_behavior(
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    return await behavior_service.get_device_behavior(db)
