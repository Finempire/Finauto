# Antigravity Tally Automation

A robust, production-grade web application tailored for accounting and finance users. Upload Excel/CSV files, map narrations to Tally ledgers using AI, and generate direct Tally-compatible XML imports.

## Features
- **Modern User Interface (React / Next.js)**: Sleek Ant Design layout with dashboards, stepper-based wizards, and real-time mapping tables.
- **AI-Powered Ledger Mapping**: Automatically suggests Chart of Accounts mappings based on transaction history and fuzzy text string matching.
- **Direct Tally Integration**: Exports format-perfect XML or pushes vouchers directly to a local/remote Tally Prime server.
- **Robust Validation**: Enforces strict Pandas dataframe checks before XML conversion.

## Tech Stack
- **Frontend**: Next.js (App Router), React, Ant Design, Tailwind CSS.
- **Backend**: Flask (Python), Pandas (Data processing), SQLAlchemy (SQLite by default).
- **Deployment**: Docker & Docker Compose.

## Structure
- `/frontend`: Next.js React application.
- `/backend`: Flask python API logic, SQLite DB models, and Tally generation services.

## Setup & Deployment
Please refer to [DEPLOY.md](DEPLOY.md) for full deployment commands using Docker, including instructions on setting environment variables from `.env.example`.
