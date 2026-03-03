"""Settings API routes."""
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from backend import db
from backend.models import (
    UserPreference, BankLedgerMaster, BankRule, UserLearnedMapping,
    TallyConnectionSetting, JournalTemplate, JournalTemplateFixedRule,
    JournalTemplateDynamicRule, load_user_settings
)

settings_bp = Blueprint('settings', __name__)


@settings_bp.route('/', methods=['GET'])
@login_required
def get_settings():
    settings = load_user_settings(current_user.email)
    return jsonify({'success': True, 'settings': settings})


@settings_bp.route('/preferences', methods=['POST'])
@login_required
def save_preferences():
    data = request.get_json()
    pref = db.session.get(UserPreference, current_user.email)
    if not pref:
        pref = UserPreference(email=current_user.email)
        db.session.add(pref)
    pref.company_name = data.get('company_name', pref.company_name)
    pref.default_suspense_ledger = data.get('default_suspense_ledger', pref.default_suspense_ledger)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Preferences saved'})


@settings_bp.route('/ledger-master', methods=['POST'])
@login_required
def save_ledger_master():
    data = request.get_json()
    ledgers = data.get('ledgers', [])
    BankLedgerMaster.query.filter_by(email=current_user.email).delete()
    for name in ledgers:
        db.session.add(BankLedgerMaster(email=current_user.email, ledger_name=name))
    db.session.commit()
    return jsonify({'success': True, 'message': f'{len(ledgers)} ledgers saved'})


@settings_bp.route('/bank-rules', methods=['GET'])
@login_required
def get_bank_rules():
    rules = BankRule.query.filter_by(email=current_user.email).all()
    return jsonify({
        'success': True,
        'rules': [{'id': r.id, 'keyword': r.keyword, 'mapped_ledger': r.mapped_ledger} for r in rules]
    })


@settings_bp.route('/bank-rules', methods=['POST'])
@login_required
def save_bank_rules():
    data = request.get_json()
    rules = data.get('rules', [])
    BankRule.query.filter_by(email=current_user.email).delete()
    for r in rules:
        db.session.add(BankRule(email=current_user.email, keyword=r.get('keyword', ''), mapped_ledger=r.get('mapped_ledger', '')))
    db.session.commit()
    return jsonify({'success': True, 'message': f'{len(rules)} rules saved'})


@settings_bp.route('/learned-mappings', methods=['POST'])
@login_required
def save_learned_mappings():
    data = request.get_json()
    mappings = data.get('mappings', {})
    for narration, mapping_data in mappings.items():
        existing = UserLearnedMapping.query.filter_by(email=current_user.email, narration_text=narration).first()
        if existing:
            existing.mapped_ledger = mapping_data.get('ledger', existing.mapped_ledger)
            existing.usage_count = existing.usage_count + 1
            existing.similarity_score = max(existing.similarity_score, mapping_data.get('score', 0))
        else:
            db.session.add(UserLearnedMapping(
                email=current_user.email,
                narration_text=narration,
                mapped_ledger=mapping_data.get('ledger', ''),
                similarity_score=mapping_data.get('score', 0),
            ))
    db.session.commit()
    return jsonify({'success': True, 'message': 'Learned mappings updated'})


@settings_bp.route('/tally-connection', methods=['POST'])
@login_required
def save_tally_connection():
    data = request.get_json()
    conn = db.session.get(TallyConnectionSetting, current_user.email)
    if not conn:
        conn = TallyConnectionSetting(email=current_user.email)
        db.session.add(conn)
    conn.tally_server_host = data.get('host', conn.tally_server_host)
    conn.tally_server_port = data.get('port', conn.tally_server_port)
    conn.tally_company_name = data.get('company_name', conn.tally_company_name)
    conn.enable_direct_sync = data.get('enable_direct_sync', conn.enable_direct_sync)
    conn.enable_direct_push_bank = data.get('enable_direct_push_bank', conn.enable_direct_push_bank)
    conn.enable_direct_push_journal = data.get('enable_direct_push_journal', conn.enable_direct_push_journal)
    conn.sync_ledgers_on_load = data.get('sync_ledgers_on_load', conn.sync_ledgers_on_load)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Tally connection settings saved'})


@settings_bp.route('/journal-template', methods=['POST'])
@login_required
def save_journal_template():
    data = request.get_json()
    template_name = data.get('template_name', '')
    fixed_rules = data.get('fixed_rules', [])
    dynamic_rules = data.get('dynamic_rules', [])

    if not template_name:
        return jsonify({'success': False, 'message': 'Template name required'}), 400

    existing = JournalTemplate.query.filter_by(email=current_user.email, template_name=template_name).first()
    if existing:
        JournalTemplateFixedRule.query.filter_by(template_id=existing.id).delete()
        JournalTemplateDynamicRule.query.filter_by(template_id=existing.id).delete()
        template = existing
    else:
        template = JournalTemplate(email=current_user.email, template_name=template_name)
        db.session.add(template)
        db.session.flush()

    for rule in fixed_rules:
        db.session.add(JournalTemplateFixedRule(
            template_id=template.id,
            csv_col=rule.get('csv_col', ''),
            tally_ledger=rule.get('tally_ledger', ''),
            type=rule.get('type', 'Debit'),
        ))
    for rule in dynamic_rules:
        db.session.add(JournalTemplateDynamicRule(
            template_id=template.id,
            ledger_name_col=rule.get('ledger_name_col', ''),
            amount_col=rule.get('amount_col', ''),
            type=rule.get('type', 'Debit'),
        ))
    db.session.commit()
    return jsonify({'success': True, 'message': f'Template "{template_name}" saved'})


@settings_bp.route('/journal-template/<int:template_id>', methods=['GET'])
@login_required
def get_journal_template(template_id):
    template = db.session.get(JournalTemplate, template_id)
    if not template or template.email != current_user.email:
        return jsonify({'success': False, 'message': 'Template not found'}), 404
    fixed = JournalTemplateFixedRule.query.filter_by(template_id=template.id).all()
    dynamic = JournalTemplateDynamicRule.query.filter_by(template_id=template.id).all()
    return jsonify({
        'success': True,
        'template': {
            'id': template.id,
            'name': template.template_name,
            'fixed_rules': [{'csv_col': r.csv_col, 'tally_ledger': r.tally_ledger, 'type': r.type} for r in fixed],
            'dynamic_rules': [{'ledger_name_col': r.ledger_name_col, 'amount_col': r.amount_col, 'type': r.type} for r in dynamic],
        }
    })


@settings_bp.route('/journal-template/<int:template_id>', methods=['DELETE'])
@login_required
def delete_journal_template(template_id):
    template = db.session.get(JournalTemplate, template_id)
    if not template or template.email != current_user.email:
        return jsonify({'success': False, 'message': 'Template not found'}), 404
    JournalTemplateFixedRule.query.filter_by(template_id=template.id).delete()
    JournalTemplateDynamicRule.query.filter_by(template_id=template.id).delete()
    db.session.delete(template)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Template deleted'})
