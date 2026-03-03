import sys
from datetime import date, timedelta
from pathlib import Path

# Ensure the application module is importable during tests
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Prevent heavy optional imports during testing
sys.modules.setdefault("sentence_transformers", None)

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

import app


class _TestConnection:
    def __init__(self, session_factory):
        self._session_factory = session_factory

    @property
    def session(self):
        return self._session_factory()


@pytest.fixture
def auth_db(tmp_path, monkeypatch):
    db_path = tmp_path / "users.db"
    engine = create_engine(f"sqlite:///{db_path}")
    Session = sessionmaker(bind=engine)
    conn = _TestConnection(Session)

    def _get_db_conn():
        return conn

    monkeypatch.setattr(app, "get_db_conn", _get_db_conn)

    with conn.session as s:
        s.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS users (
                    email TEXT PRIMARY KEY,
                    name TEXT,
                    phone TEXT,
                    password_hash TEXT,
                    signup_date DATE,
                    subscription_expiry_date DATE DEFAULT NULL
                );
                """
            )
        )
        s.commit()

    return conn


def _insert_user(conn, email, password, signup_date, subscription_expiry_date=None):
    with conn.session as s:
        s.execute(
            text(
                """
                INSERT INTO users (email, name, phone, password_hash, signup_date, subscription_expiry_date)
                VALUES (:email, :name, :phone, :password_hash, :signup_date, :subscription_expiry_date)
                """
            ),
            params={
                "email": email,
                "name": "Test User",
                "phone": "0000000000",
                "password_hash": app.hash_password(password),
                "signup_date": signup_date.isoformat(),
                "subscription_expiry_date": subscription_expiry_date.isoformat()
                if subscription_expiry_date
                else None,
            },
        )
        s.commit()


def test_trial_user_returns_trial(auth_db):
    signup_date = date.today()
    _insert_user(auth_db, "trial@example.com", "trialpass", signup_date)

    status = app.check_user_status("trial@example.com", "trialpass")

    assert status == "TRIAL"


def test_paid_user_returns_paid(auth_db):
    signup_date = date.today() - timedelta(days=60)
    expiry_date = date.today() + timedelta(days=15)
    _insert_user(auth_db, "paid@example.com", "paidpass", signup_date, expiry_date)

    status = app.check_user_status("paid@example.com", "paidpass")

    assert status == "PAID"


def test_invalid_user_returns_invalid(auth_db):
    signup_date = date.today()
    _insert_user(auth_db, "invalid@example.com", "validpass", signup_date)

    status = app.check_user_status("invalid@example.com", "wrongpass")

    assert status == "INVALID"
