# FinAuto v2.0

**Tally ERP Automation Platform** — Upload Excel, Push to Tally.

## Architecture

- **Backend**: FastAPI (Python 3.11), SQLAlchemy 2.0, PostgreSQL
- **Frontend**: React 18 + TypeScript + Vite + Tailwind CSS
- **Infrastructure**: Docker Compose (nginx + backend + postgres)
- **Auth**: JWT (8-hour tokens)

## Quick Start (Local Dev)

```bash
# Backend
cd backend
python -m venv venv && venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install && npm run dev
```

## Deploy to Linode

```bash
ssh root@your-linode-ip
git clone https://github.com/Finempire/Finauto.git /app && cd /app
cp .env.example .env  # edit with real secrets
cd frontend && npm install && npm run build && cd ..
docker compose up -d
```

## Default Admin

- Email: `admin@finauto.com`
- Password: set via `ADMIN_PASSWORD` in `.env`
