from fastapi import APIRouter, Depends
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.dependencies import get_db
from app.models.security_alert import SecurityAlert
from app.schemas.alert import AlertResponse

router = APIRouter(prefix="/alerts", tags=["Security Alerts"])


@router.get("/", response_model=list[AlertResponse])
async def get_alerts(
    db: AsyncSession = Depends(get_db),
) -> list[SecurityAlert]:
    result = await db.execute(
        select(SecurityAlert).order_by(
            SecurityAlert.created_at.desc()
        )
    )
    return list(result.scalars().all())
@router.patch("/{alert_id}/status")
async def update_alert_status(
    alert_id: int,
    status: str,
    db: AsyncSession = Depends(get_db),
):
    if status not in {"new", "acknowledged", "resolved"}:
        raise HTTPException(
            status_code=400,
            detail="Invalid alert status.",
        )

    alert = await db.get(SecurityAlert, alert_id)

    if not alert:
        raise HTTPException(
            status_code=404,
            detail="Alert not found.",
        )

    alert.status = status

    await db.commit()
    await db.refresh(alert)

    return alert
