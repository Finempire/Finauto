from datetime import date
from flask import Blueprint, request, jsonify, session
from flask_login import login_user, logout_user, login_required, current_user
from backend import db
from backend.models import (
    User, hash_password, check_user_status, load_user_settings, activate_user_payment
)

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = (data.get('email') or '').strip().lower()
    password = data.get('password', '')

    if not email or not password:
        return jsonify({'success': False, 'message': 'Email and password are required'}), 400

    status = check_user_status(email, password)

    if status == 'INVALID':
        return jsonify({'success': False, 'message': 'Invalid email or password'}), 401

    user = db.session.get(User, email)
    login_user(user, remember=True)

    settings = load_user_settings(email)

    return jsonify({
        'success': True,
        'status': status,
        'user': {
            'email': user.email,
            'name': user.name,
            'phone': user.phone,
            'signup_date': user.signup_date.isoformat() if user.signup_date else None,
            'subscription_expiry': user.subscription_expiry_date.isoformat() if user.subscription_expiry_date else None,
            'status': status,
        },
        'settings': settings,
    })


@auth_bp.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    email = (data.get('email') or '').strip().lower()
    name = (data.get('name') or '').strip()
    phone = (data.get('phone') or '').strip()
    password = data.get('password', '')

    if not all([email, name, phone, password]):
        return jsonify({'success': False, 'message': 'All fields are required'}), 400

    if len(password) < 6:
        return jsonify({'success': False, 'message': 'Password must be at least 6 characters'}), 400

    existing = db.session.get(User, email)
    if existing:
        return jsonify({'success': False, 'message': 'An account with this email already exists'}), 409

    try:
        user = User(
            email=email,
            name=name,
            phone=phone,
            password_hash=hash_password(password),
            signup_date=date.today(),
        )
        db.session.add(user)
        db.session.commit()
        login_user(user, remember=True)
        return jsonify({
            'success': True,
            'message': 'Account created successfully! 30-day free trial activated.',
            'user': {
                'email': user.email,
                'name': user.name,
            }
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Registration failed: {str(e)}'}), 500


@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return jsonify({'success': True, 'message': 'Logged out'})


@auth_bp.route('/me', methods=['GET'])
@login_required
def me():
    user = current_user
    settings = load_user_settings(user.email)
    today = date.today()

    # Determine status
    status = 'PENDING'
    if user.subscription_expiry_date and today <= user.subscription_expiry_date:
        status = 'PAID'
    elif user.signup_date:
        from datetime import timedelta
        if today <= user.signup_date + timedelta(days=30):
            status = 'TRIAL'

    return jsonify({
        'success': True,
        'user': {
            'email': user.email,
            'name': user.name,
            'phone': user.phone,
            'signup_date': user.signup_date.isoformat() if user.signup_date else None,
            'subscription_expiry': user.subscription_expiry_date.isoformat() if user.subscription_expiry_date else None,
            'status': status,
        },
        'settings': settings,
    })
