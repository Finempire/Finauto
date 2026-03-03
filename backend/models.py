import hashlib
from datetime import date, datetime, timedelta
import bcrypt
from flask_login import UserMixin
from backend import db


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    email = db.Column(db.String, primary_key=True)
    name = db.Column(db.String)
    phone = db.Column(db.String)
    password_hash = db.Column(db.String)
    signup_date = db.Column(db.Date)
    subscription_expiry_date = db.Column(db.Date, default=None)

    def get_id(self):
        return self.email


class UserPreference(db.Model):
    __tablename__ = 'user_preferences'
    email = db.Column(db.String, db.ForeignKey('users.email'), primary_key=True)
    company_name = db.Column(db.String)
    default_suspense_ledger = db.Column(db.String)


class JournalTemplate(db.Model):
    __tablename__ = 'journal_templates'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String, db.ForeignKey('users.email'))
    template_name = db.Column(db.String)
    __table_args__ = (db.UniqueConstraint('email', 'template_name'),)


class JournalTemplateFixedRule(db.Model):
    __tablename__ = 'journal_template_fixed_rules'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    template_id = db.Column(db.Integer, db.ForeignKey('journal_templates.id', ondelete='CASCADE'))
    csv_col = db.Column(db.String)
    tally_ledger = db.Column(db.String)
    type = db.Column(db.String)


class JournalTemplateDynamicRule(db.Model):
    __tablename__ = 'journal_template_dynamic_rules'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    template_id = db.Column(db.Integer, db.ForeignKey('journal_templates.id', ondelete='CASCADE'))
    ledger_name_col = db.Column(db.String)
    amount_col = db.Column(db.String)
    type = db.Column(db.String)


class BankLedgerMaster(db.Model):
    __tablename__ = 'bank_ledger_master'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String, db.ForeignKey('users.email'))
    ledger_name = db.Column(db.String)


class BankRule(db.Model):
    __tablename__ = 'bank_rules'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String, db.ForeignKey('users.email'))
    keyword = db.Column(db.String)
    mapped_ledger = db.Column(db.String)


class UserLearnedMapping(db.Model):
    __tablename__ = 'user_learned_mappings'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String, db.ForeignKey('users.email'))
    narration_text = db.Column(db.String)
    mapped_ledger = db.Column(db.String)
    similarity_score = db.Column(db.Float, default=0)
    usage_count = db.Column(db.Integer, default=1)
    last_used = db.Column(db.Date, default=date.today)
    __table_args__ = (db.UniqueConstraint('email', 'narration_text'),)


class TallyConnectionSetting(db.Model):
    __tablename__ = 'tally_connection_settings'
    email = db.Column(db.String, db.ForeignKey('users.email'), primary_key=True)
    tally_server_host = db.Column(db.String, default='localhost')
    tally_server_port = db.Column(db.Integer, default=9000)
    tally_company_name = db.Column(db.String)
    enable_direct_sync = db.Column(db.Boolean, default=False)
    enable_direct_push_bank = db.Column(db.Boolean, default=False)
    enable_direct_push_journal = db.Column(db.Boolean, default=False)
    sync_ledgers_on_load = db.Column(db.Boolean, default=False)
    last_sync_date = db.Column(db.DateTime)


class TallySyncedLedger(db.Model):
    __tablename__ = 'tally_synced_ledgers'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String, db.ForeignKey('users.email'))
    ledger_name = db.Column(db.String)
    ledger_group = db.Column(db.String)
    sync_date = db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__ = (db.UniqueConstraint('email', 'ledger_name'),)


# --- Password helpers ---

def hash_password(password):
    return bcrypt.hashpw(str(password).encode(), bcrypt.gensalt()).decode()


def _legacy_hash_password(password):
    return hashlib.sha256(str(password).encode()).hexdigest()


def verify_password(password, stored_hash):
    if not stored_hash:
        return False, False
    password_bytes = str(password).encode()
    if stored_hash.startswith('$2'):
        try:
            return bcrypt.checkpw(password_bytes, stored_hash.encode()), False
        except ValueError:
            return False, False
    if len(stored_hash) == 64 and all(c in '0123456789abcdef' for c in stored_hash.lower()):
        legacy_hash = _legacy_hash_password(password)
        return legacy_hash == stored_hash, True
    return False, False


def check_user_status(email, password):
    """Check credentials and return status string."""
    user = db.session.get(User, email)
    if not user:
        return 'INVALID'
    try:
        is_valid, needs_upgrade = verify_password(password, user.password_hash)
    except Exception:
        return 'INVALID'
    if not is_valid:
        return 'INVALID'
    if needs_upgrade:
        try:
            user.password_hash = hash_password(password)
            db.session.commit()
        except Exception:
            db.session.rollback()

    today = date.today()
    if user.subscription_expiry_date:
        if today <= user.subscription_expiry_date:
            return 'PAID'
    if user.signup_date:
        trial_expiry = user.signup_date + timedelta(days=30)
        if today <= trial_expiry:
            return 'TRIAL'
    return 'PENDING'


def activate_user_payment(email):
    """Adds 30 days of access."""
    user = db.session.get(User, email)
    if not user:
        return False
    today = date.today()
    base_date = today
    if user.subscription_expiry_date and user.subscription_expiry_date > today:
        base_date = user.subscription_expiry_date
    user.subscription_expiry_date = base_date + timedelta(days=30)
    db.session.commit()
    return True


def load_user_settings(email):
    """Load all settings for a user into a dict."""
    settings = {
        'company_name': 'Xml2Tally (Default Co.)',
        'ledger_master': ['Bank Suspense A/c (Default)'],
        'bank_rules': [],
        'default_suspense_ledger': 'Bank Suspense A/c (Default)',
        'learned_mappings': {},
        'journal_templates': {},
        'tally_server_host': 'localhost',
        'tally_server_port': 9000,
        'tally_company_name': '',
        'enable_direct_sync': False,
        'enable_direct_push_bank': False,
        'enable_direct_push_journal': False,
        'sync_ledgers_on_load': False,
    }

    pref = db.session.get(UserPreference, email)
    if pref:
        settings['company_name'] = pref.company_name or settings['company_name']
        settings['default_suspense_ledger'] = pref.default_suspense_ledger or settings['default_suspense_ledger']

    templates = JournalTemplate.query.filter_by(email=email).all()
    settings['journal_templates'] = {t.template_name: t.id for t in templates}

    ledgers = BankLedgerMaster.query.filter_by(email=email).all()
    if ledgers:
        settings['ledger_master'] = [l.ledger_name for l in ledgers]

    rules = BankRule.query.filter_by(email=email).all()
    settings['bank_rules'] = [{'Narration Keyword': r.keyword, 'Mapped Ledger': r.mapped_ledger} for r in rules]

    mappings = UserLearnedMapping.query.filter_by(email=email).all()
    settings['learned_mappings'] = {
        m.narration_text: {'ledger': m.mapped_ledger, 'score': m.similarity_score, 'count': m.usage_count}
        for m in mappings
    }

    tally_conn = db.session.get(TallyConnectionSetting, email)
    if tally_conn:
        settings['tally_server_host'] = tally_conn.tally_server_host or 'localhost'
        settings['tally_server_port'] = tally_conn.tally_server_port or 9000
        settings['tally_company_name'] = tally_conn.tally_company_name or ''
        settings['enable_direct_sync'] = bool(tally_conn.enable_direct_sync)
        settings['enable_direct_push_bank'] = bool(tally_conn.enable_direct_push_bank)
        settings['enable_direct_push_journal'] = bool(tally_conn.enable_direct_push_journal)
        settings['sync_ledgers_on_load'] = bool(tally_conn.sync_ledgers_on_load)

    return settings


def init_database(app):
    """Seed default admin if enabled."""
    if not app.config.get('SEED_DEFAULT_ADMIN', True):
        return
    admin = db.session.get(User, 'admin')
    if admin:
        return
    try:
        admin_pass = app.config.get('ADMIN_DEFAULT_PASSWORD', 'admin@2003')
        admin_user = User(
            email='admin',
            name='Administrator',
            phone='0000000000',
            password_hash=hash_password(admin_pass),
            signup_date=date.today(),
            subscription_expiry_date=date.today() + timedelta(days=36500),
        )
        db.session.add(admin_user)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        import logging
        logging.getLogger(__name__).error(f'Admin user creation: {e}')
