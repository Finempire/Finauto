import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_cors import CORS

db = SQLAlchemy()
login_manager = LoginManager()


def create_app():
    app = Flask(__name__)

    # Load config
    app.config.from_object('config.Config')

    # Enable CORS for frontend dev server
    CORS(app, supports_credentials=True, origins=["http://localhost:3000", "http://127.0.0.1:3000"])

    # Ensure data directory exists
    os.makedirs('data', exist_ok=True)
    # Init extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login_page'

    # User loader
    from backend.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, user_id)

    @login_manager.unauthorized_handler
    def unauthorized():
        from flask import jsonify
        return jsonify({'success': False, 'message': 'Authentication required'}), 401

    # Register blueprints
    from backend.auth.routes import auth_bp
    from backend.tally.routes import tally_bp
    from backend.settings.routes import settings_bp
    from backend.payment.routes import payment_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(tally_bp, url_prefix='/api/tally')
    app.register_blueprint(settings_bp, url_prefix='/api/settings')
    app.register_blueprint(payment_bp, url_prefix='/api/payment')

    # Create tables and seed admin
    with app.app_context():
        from backend.models import init_database
        db.create_all()
        init_database(app)

    return app
