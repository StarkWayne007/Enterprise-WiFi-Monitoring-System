from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.dependencies import get_db
from app.models.device import Device
from app.schemas.device import DeviceCreate, DeviceResponse, DeviceUpdate

router = APIRouter(prefix="/devices", tags=["Devices"])


@router.get("/", response_model=list[DeviceResponse])
async def get_devices(
    db: AsyncSession = Depends(get_db),
) -> list[Device]:
    result = await db.execute(select(Device))
    return list(result.scalars().all())


@router.post(
    "/",
    response_model=DeviceResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_device(
    device_data: DeviceCreate,
    db: AsyncSession = Depends(get_db),
) -> Device:
    device = Device(**device_data.model_dump())

    db.add(device)

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A device with this MAC address already exists.",
        )

    await db.refresh(device)

    return device

@router.put("/{device_id}", response_model=DeviceResponse)
async def update_device(
    device_id: int,
    device_data: DeviceUpdate,
    db: AsyncSession = Depends(get_db),
) -> Device:
    device = await db.get(Device, device_id)

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found.",
        )

    for field, value in device_data.model_dump(exclude_unset=True).items():
        setattr(device, field, value)

    await db.commit()
    await db.refresh(device)

    return device


@router.delete("/{device_id}")
async def delete_device(device_id: int, db: AsyncSession = Depends(get_db)):
    device = await db.get(Device, device_id)

    if not device:
        raise HTTPException(
            status_code=404,
            detail="Device not found.",
        )

    await db.delete(device)
    await db.commit()

    return {"message": "Device deleted successfully."}

