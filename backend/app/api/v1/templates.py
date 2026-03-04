import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.mapping_template import MappingTemplate
from app.models.user import User
from app.schemas import MappingTemplateOut, MappingTemplateCreate

router = APIRouter(prefix="/api/templates", tags=["templates"])


@router.get("/", response_model=list[MappingTemplateOut])
async def list_templates(
    voucher_type: str | None = None,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    query = select(MappingTemplate).order_by(MappingTemplate.created_at.desc())
    if voucher_type:
        query = query.where(MappingTemplate.voucher_type == voucher_type)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/", response_model=MappingTemplateOut, status_code=201)
async def create_template(
    body: MappingTemplateCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    template = MappingTemplate(**body.model_dump(), created_by=user.id)
    db.add(template)
    await db.flush()
    await db.refresh(template)
    return template


@router.delete("/{template_id}", status_code=204)
async def delete_template(
    template_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    result = await db.execute(select(MappingTemplate).where(MappingTemplate.id == template_id))
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    await db.delete(template)
