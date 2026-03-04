import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.tally_config import TallyConfig
from app.models.user import User
from app.schemas import TallyConfigOut, TallyConfigCreate, TallyConfigUpdate, TallyPingRequest
from app.services.tally_client import ping_tally, fetch_companies

router = APIRouter(prefix="/api/tally", tags=["tally"])


@router.get("/configs", response_model=list[TallyConfigOut])
async def list_configs(db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    result = await db.execute(select(TallyConfig).order_by(TallyConfig.created_at.desc()))
    return result.scalars().all()


@router.post("/configs", response_model=TallyConfigOut, status_code=201)
async def create_config(
    body: TallyConfigCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    config = TallyConfig(**body.model_dump(), created_by=user.id)
    db.add(config)
    await db.flush()
    await db.refresh(config)
    return config


@router.patch("/configs/{config_id}", response_model=TallyConfigOut)
async def update_config(
    config_id: uuid.UUID,
    body: TallyConfigUpdate,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    result = await db.execute(select(TallyConfig).where(TallyConfig.id == config_id))
    config = result.scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=404, detail="Tally config not found")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(config, field, value)

    await db.flush()
    await db.refresh(config)
    return config


@router.delete("/configs/{config_id}", status_code=204)
async def delete_config(
    config_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    result = await db.execute(select(TallyConfig).where(TallyConfig.id == config_id))
    config = result.scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=404, detail="Tally config not found")
    await db.delete(config)


@router.post("/ping")
async def ping(body: TallyPingRequest, _=Depends(get_current_user)):
    reachable, message = await ping_tally(body.host, body.port)
    return {"reachable": reachable, "message": message}


@router.get("/companies")
async def companies(host: str = "localhost", port: int = 9000, _=Depends(get_current_user)):
    company_list = await fetch_companies(host, port)
    return {"companies": company_list}
