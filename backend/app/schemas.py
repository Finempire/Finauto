import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr


# ─── Auth ───────────────────────────────────────────────────────
class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ─── User ───────────────────────────────────────────────────────
class UserOut(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str | None
    role: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    email: str
    password: str
    full_name: str | None = None
    role: str = "operator"


class UserUpdate(BaseModel):
    full_name: str | None = None
    role: str | None = None
    is_active: bool | None = None


# ─── Tally Config ──────────────────────────────────────────────
class TallyConfigOut(BaseModel):
    id: uuid.UUID
    label: str
    host: str
    port: int
    company_name: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class TallyConfigCreate(BaseModel):
    label: str
    host: str = "localhost"
    port: int = 9000
    company_name: str | None = None


class TallyConfigUpdate(BaseModel):
    label: str | None = None
    host: str | None = None
    port: int | None = None
    company_name: str | None = None


class TallyPingRequest(BaseModel):
    host: str = "localhost"
    port: int = 9000


# ─── Mapping Template ──────────────────────────────────────────
class MappingTemplateOut(BaseModel):
    id: uuid.UUID
    name: str
    voucher_type: str
    mapping_json: dict
    created_at: datetime

    class Config:
        from_attributes = True


class MappingTemplateCreate(BaseModel):
    name: str
    voucher_type: str
    mapping_json: dict


# ─── Upload ─────────────────────────────────────────────────────
class ParseResponse(BaseModel):
    headers: list[str]
    preview_rows: list[dict]
    suggested_mapping: dict[str, str]
    total_rows: int


class ValidateRequest(BaseModel):
    mapping: dict[str, str]
    voucher_type: str
    skip_invalid: bool = False


class ValidateResponse(BaseModel):
    total_rows: int
    valid_rows: int
    error_rows: int
    errors: list[dict]
    preview: list[dict]


class PushRequest(BaseModel):
    mapping: dict[str, str]
    voucher_type: str
    tally_config_id: uuid.UUID
    skip_errors: bool = False
