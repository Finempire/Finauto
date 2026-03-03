import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'xml2tally-secret-key-change-in-production')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', f'sqlite:///{os.path.join(BASE_DIR, "data", "users.db")}')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Razorpay
    RAZORPAY_KEY_ID = os.getenv('RAZORPAY_KEY_ID', 'YOUR_KEY_ID_HERE')
    RAZORPAY_KEY_SECRET = os.getenv('RAZORPAY_KEY_SECRET', 'YOUR_KEY_SECRET_HERE')

    # Admin
    SEED_DEFAULT_ADMIN = os.getenv('SEED_DEFAULT_ADMIN', 'true').lower() in {'1', 'true', 'yes', 'on'}
    ADMIN_DEFAULT_PASSWORD = os.getenv('ADMIN_DEFAULT_PASSWORD', 'admin@2003')
