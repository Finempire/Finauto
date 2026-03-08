from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from passlib.context import CryptContext
from sqlalchemy import select

from app.config import settings
from app.database import engine, Base, async_session
from app.models import User, TallyConfig, MappingTemplate
from app.api.v1.auth import router as auth_router
from app.api.v1.admin import router as admin_router
from app.api.v1.upload import router as upload_router
from app.api.v1.tally import router as tally_router
from app.api.v1.templates import router as templates_router

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


async def seed_admin():
    """Create default admin user if none exists."""
    async with async_session() as session:
        result = await session.execute(select(User).where(User.role == "admin"))
        if not result.scalar_one_or_none():
            admin = User(
                email=settings.ADMIN_EMAIL,
                hashed_pw=pwd_context.hash(settings.ADMIN_PASSWORD),
                full_name="Admin",
                role="admin",
            )
            session.add(admin)
            await session.commit()
            print(f"[FinAuto] Default admin created: {settings.ADMIN_EMAIL}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables + seed admin
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await seed_admin()
    yield
    # Shutdown
    await engine.dispose()


app = FastAPI(
    title="FinAuto API",
    version="2.0.0",
    description="Tally ERP Automation — Upload Excel, Push to Tally",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(upload_router)
app.include_router(tally_router)
app.include_router(templates_router)


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "2.0.0"}
