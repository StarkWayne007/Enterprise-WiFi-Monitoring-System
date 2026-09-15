from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.dependencies import get_db
from app.services.reporting import ReportingService

router = APIRouter(prefix="/reports", tags=["Reports"])

reporting_service = ReportingService()


@router.get("/summary")
async def get_report_summary(
    db: AsyncSession = Depends(get_db),
):
    return await reporting_service.get_report_summary(db)

@router.get("/detail")
async def get_report_detail(
    db: AsyncSession = Depends(get_db),
):
    return await reporting_service.get_report_detail(db)


