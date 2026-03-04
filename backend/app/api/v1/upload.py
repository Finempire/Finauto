import io
import json
import uuid

from fastapi import APIRouter, Depends, File, Form, UploadFile, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.tally_config import TallyConfig
from app.models.user import User
from app.schemas import ParseResponse
from app.services.excel_parser import parse_excel
from app.services.column_mapper import suggest_mapping
from app.services.validator import validate_rows
from app.services.tally_client import push_vouchers

router = APIRouter(prefix="/api/upload", tags=["upload"])

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_ROWS = 5000


@router.post("/parse", response_model=ParseResponse)
async def parse(
    file: UploadFile = File(...),
    _: User = Depends(get_current_user),
):
    if not file.filename or not file.filename.lower().endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="Only .xlsx and .xls files are accepted")

    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File size exceeds 10MB limit")

    headers, all_rows = parse_excel(contents)
    if len(all_rows) > MAX_ROWS:
        raise HTTPException(status_code=400, detail=f"File has {len(all_rows)} rows. Maximum is {MAX_ROWS}.")

    preview = all_rows[:20]
    mapping = suggest_mapping(headers)

    return ParseResponse(
        headers=headers,
        preview_rows=preview,
        suggested_mapping=mapping,
        total_rows=len(all_rows),
    )


@router.post("/validate")
async def validate(
    file: UploadFile = File(...),
    mapping: str = Form(...),
    voucher_type: str = Form(...),
    _: User = Depends(get_current_user),
):
    contents = await file.read()
    mapping_dict = json.loads(mapping)
    _, all_rows = parse_excel(contents)

    errors, valid_count = validate_rows(all_rows, mapping_dict, voucher_type)

    return {
        "total_rows": len(all_rows),
        "valid_rows": valid_count,
        "error_rows": len(errors),
        "errors": errors,
        "preview": all_rows[:50],
    }


@router.post("/push")
async def push(
    file: UploadFile = File(...),
    mapping: str = Form(...),
    voucher_type: str = Form(...),
    tally_config_id: str = Form(...),
    skip_errors: str = Form("false"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    contents = await file.read()
    mapping_dict = json.loads(mapping)
    config_id = uuid.UUID(tally_config_id)
    skip = skip_errors.lower() == "true"

    result = await db.execute(select(TallyConfig).where(TallyConfig.id == config_id))
    config = result.scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=404, detail="Tally config not found")

    _, all_rows = parse_excel(contents)

    async def event_stream():
        async for event in push_vouchers(all_rows, mapping_dict, voucher_type, config, skip):
            yield f"data: {json.dumps(event)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
