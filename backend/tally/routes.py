"""Tally API routes — upload, convert, sync, push, fetch companies."""
import io
import pandas as pd
from flask import Blueprint, request, jsonify, session
from flask_login import login_required, current_user

from backend.tally.xml_journal import create_tally_xml, get_template_csv
from backend.tally.xml_bank import create_bank_tally_xml, get_bank_template_csv
from backend.tally.xml_sales import create_sales_tally_xml, get_sales_template_csv
from backend.tally.xml_credit_note import create_credit_note_tally_xml, get_credit_note_template_csv
from backend.tally.tally_comm import (
    check_tally_alive, sync_ledgers_from_tally, push_vouchers_to_tally,
    fetch_companies_from_tally, get_synced_ledgers
)
from backend.ai.mapper import get_smart_suggestions, auto_map_ledgers_based_on_rules
from backend.models import load_user_settings
from backend.services.validation import ValidationService

tally_bp = Blueprint('tally', __name__)


def _load_file(file_storage):
    """Read uploaded CSV/XLSX into a DataFrame."""
    filename = file_storage.filename.lower()
    if filename.endswith('.csv'):
        return pd.read_csv(file_storage)
    elif filename.endswith(('.xlsx', '.xls')):
        return pd.read_excel(file_storage)
    return None


# ---------- File upload ----------

@tally_bp.route('/upload', methods=['POST'])
@login_required
def upload_file():
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file uploaded'}), 400
    f = request.files['file']
    if not f.filename:
        return jsonify({'success': False, 'message': 'No file selected'}), 400
    try:
        # Prevent pandas encoding errors by handling multiple encodings
        try:
            df = _load_file(f)
        except UnicodeDecodeError:
            f.seek(0)
            df = pd.read_csv(f, encoding='latin1')

        if df is None:
            return jsonify({'success': False, 'message': 'Unsupported file type. Use CSV or XLSX'}), 400

        is_valid, errors = ValidationService.validate_bank_upload(df)
        if not is_valid:
            return jsonify({'success': False, 'message': 'Validation failed', 'errors': errors}), 400

        columns = df.columns.tolist()
        # Return ALL rows so frontend can use them for XML generation
        all_rows = df.fillna('').to_dict(orient='records')
        return jsonify({
            'success': True,
            'columns': columns,
            'preview': all_rows,
            'row_count': len(df),
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'File processing error: {str(e)}'}), 500



# ---------- AI ledger mapping ----------

@tally_bp.route('/ai-map', methods=['POST'])
@login_required
def ai_map():
    data = request.get_json()
    narrations = data.get('narrations', [])
    if not narrations:
        return jsonify({'success': False, 'message': 'No narrations provided'}), 400

    settings = load_user_settings(current_user.email)
    ledger_master = settings.get('ledger_master', [])
    rules = settings.get('bank_rules', [])
    suspense = settings.get('default_suspense_ledger', 'Bank Suspense A/c (Default)')
    learned = settings.get('learned_mappings', {})

    # Merge with Tally synced ledgers for richer suggestions
    synced = get_synced_ledgers(current_user.email)
    synced_names = [row[0] for row in synced]
    merged_ledgers = list(dict.fromkeys(ledger_master + synced_names))

    matches, scores, types = get_smart_suggestions(narrations, merged_ledgers, rules, suspense, learned)
    return jsonify({'success': True, 'matches': matches, 'scores': scores, 'types': types})


@tally_bp.route('/auto-map', methods=['POST'])
@login_required
def auto_map():
    data = request.get_json()
    narrations = data.get('narrations', [])
    if not narrations:
        return jsonify({'success': False, 'message': 'No narrations provided'}), 400
    settings = load_user_settings(current_user.email)

    # Merge ledger_master + Tally synced ledgers for maximum coverage
    ledger_master = settings.get('ledger_master', [])
    synced = get_synced_ledgers(current_user.email)
    synced_names = [row[0] for row in synced]
    merged_ledgers = list(dict.fromkeys(ledger_master + synced_names))

    mappings = auto_map_ledgers_based_on_rules(
        narrations,
        merged_ledgers,
        settings.get('bank_rules', []),
        settings.get('default_suspense_ledger', 'Bank Suspense A/c (Default)'),
        settings.get('learned_mappings', {})
    )
    return jsonify({'success': True, 'mappings': mappings, 'ledger_count': len(merged_ledgers)})


# ---------- Smart Rules from Tally ----------

@tally_bp.route('/smart-rules', methods=['GET'])
@login_required
def get_smart_rules():
    """
    Returns smart ledger mapping rules derived from Tally synced ledgers
    + existing user bank_rules. Used to populate Auto Map suggestions.
    """
    settings = load_user_settings(current_user.email)
    synced = get_synced_ledgers(current_user.email)

    smart_rules = []
    seen_keywords = set()

    for ledger_name, ledger_group, _ in synced:
        if not ledger_name:
            continue
        keyword = ledger_name.lower().strip()
        # Skip very short or overly generic names
        if len(keyword) < 3 or keyword in ('bank', 'cash', 'gst', 'tds'):
            continue
        if keyword not in seen_keywords:
            seen_keywords.add(keyword)
            smart_rules.append({
                'keyword': ledger_name,
                'mapped_ledger': ledger_name,
                'group': ledger_group or '',
                'source': 'tally_sync',
            })

    # Also include existing user-defined bank rules
    user_rules = settings.get('bank_rules', [])
    for r in user_rules:
        kw = r.get('Narration Keyword', '').lower()
        if kw and kw not in seen_keywords:
            seen_keywords.add(kw)
            smart_rules.append({
                'keyword': r.get('Narration Keyword', ''),
                'mapped_ledger': r.get('Mapped Ledger', ''),
                'group': '',
                'source': 'user_rule',
            })

    # Return full synced ledger list for dropdown population
    all_ledgers = [{'name': row[0], 'group': row[1] or ''} for row in synced]

    return jsonify({
        'success': True,
        'smart_rules': smart_rules,
        'all_ledgers': all_ledgers,
        'rule_count': len(smart_rules),
        'ledger_count': len(all_ledgers),
    })


# ---------- XML generation ----------

@tally_bp.route('/generate/journal', methods=['POST'])
@login_required
def generate_journal():
    data = request.get_json()
    rows = data.get('rows', [])
    fixed_config = data.get('fixed_ledger_config', [])
    dynamic_config = data.get('dynamic_ledger_config', [])
    company_name = data.get('company_name', '')
    voucher_type = data.get('voucher_type', 'Journal')
    journal_mappings = data.get('journal_mappings', {})

    if not rows:
        return jsonify({'success': False, 'message': 'No data to process'}), 400

    df = pd.DataFrame(rows)
    mapping_dfs = {}
    for col, mapping_list in journal_mappings.items():
        mapping_dfs[col] = pd.DataFrame(mapping_list)

    xml, errors = create_tally_xml(df, fixed_config, dynamic_config, company_name, voucher_type, mapping_dfs)
    voucher_count = xml.count('<TALLYMESSAGE')
    return jsonify({'success': True, 'xml': xml, 'voucher_count': voucher_count, 'errors': errors})


@tally_bp.route('/generate/bank', methods=['POST'])
@login_required
def generate_bank():
    data = request.get_json()
    rows = data.get('rows', [])
    bank_ledger = data.get('bank_ledger', '')
    company_name = data.get('company_name', '')

    if not rows:
        return jsonify({'success': False, 'message': 'No data to process'}), 400

    is_valid, errors = ValidationService.validate_bank_mapping(rows)
    if not is_valid:
        return jsonify({'success': False, 'message': 'Validation Failed', 'errors': errors}), 400

    df = pd.DataFrame(rows)
    xml, errors = create_bank_tally_xml(df, bank_ledger, company_name)
    voucher_count = xml.count('<TALLYMESSAGE')
    return jsonify({'success': True, 'xml': xml, 'voucher_count': voucher_count, 'errors': errors})


@tally_bp.route('/generate/sales', methods=['POST'])
@login_required
def generate_sales():
    data = request.get_json()
    rows = data.get('rows', [])
    company_name = data.get('company_name', '')
    sgst = data.get('sgst_ledger', 'Output SGST@2.5%')
    cgst = data.get('cgst_ledger', 'Output CGST@2.5%')
    igst = data.get('igst_ledger', 'Output IGST@5%')

    if not rows:
        return jsonify({'success': False, 'message': 'No data to process'}), 400

    df = pd.DataFrame(rows)
    xml, errors = create_sales_tally_xml(df, company_name, sgst, cgst, igst)
    voucher_count = xml.count('<TALLYMESSAGE')
    return jsonify({'success': True, 'xml': xml, 'voucher_count': voucher_count, 'errors': errors})


@tally_bp.route('/generate/credit-note', methods=['POST'])
@login_required
def generate_credit_note():
    data = request.get_json()
    rows = data.get('rows', [])
    company_name = data.get('company_name', '')
    sgst = data.get('sgst_ledger', 'Output SGST@2.5%')
    cgst = data.get('cgst_ledger', 'Output CGST@2.5%')
    igst = data.get('igst_ledger', 'Output IGST@5%')

    if not rows:
        return jsonify({'success': False, 'message': 'No data to process'}), 400

    df = pd.DataFrame(rows)
    xml, errors = create_credit_note_tally_xml(df, company_name, sgst, cgst, igst)
    voucher_count = xml.count('<TALLYMESSAGE')
    return jsonify({'success': True, 'xml': xml, 'voucher_count': voucher_count, 'errors': errors})


# ---------- Templates ----------

@tally_bp.route('/template/bank', methods=['GET'])
@login_required
def bank_template():
    return jsonify({'success': True, 'csv': get_bank_template_csv()})


@tally_bp.route('/template/sales', methods=['GET'])
@login_required
def sales_template():
    return jsonify({'success': True, 'csv': get_sales_template_csv()})


@tally_bp.route('/template/credit-note', methods=['GET'])
@login_required
def credit_note_template():
    return jsonify({'success': True, 'csv': get_credit_note_template_csv()})


@tally_bp.route('/template/journal', methods=['POST'])
@login_required
def journal_template():
    data = request.get_json()
    fixed = data.get('fixed_ledger_config', [])
    dynamic = data.get('dynamic_ledger_config', [])
    return jsonify({'success': True, 'csv': get_template_csv(fixed, dynamic)})


# ---------- Tally server communication ----------

@tally_bp.route('/check-alive', methods=['POST'])
@login_required
def tally_alive():
    data = request.get_json()
    host = data.get('host', 'localhost')
    port = data.get('port', 9000)
    alive, message, resolved_host = check_tally_alive(host, port)
    return jsonify({'success': alive, 'message': message, 'resolved_host': resolved_host})


@tally_bp.route('/sync-ledgers', methods=['POST'])
@login_required
def sync_ledgers():
    data = request.get_json()
    host = data.get('host', 'localhost')
    port = data.get('port', 9000)
    company = data.get('company_name', '')
    success, message, count = sync_ledgers_from_tally(host, port, company, current_user.email)
    return jsonify({'success': success, 'message': message, 'count': count})


@tally_bp.route('/push', methods=['POST'])
@login_required
def push_vouchers():
    data = request.get_json()
    xml = data.get('xml', '')
    host = data.get('host', 'localhost')
    port = data.get('port', 9000)
    if not xml:
        return jsonify({'success': False, 'message': 'No XML data provided'}), 400
    success, message, count = push_vouchers_to_tally(xml, host, port)
    return jsonify({'success': success, 'message': message, 'count': count})


@tally_bp.route('/companies', methods=['POST'])
@login_required
def fetch_companies():
    data = request.get_json()
    host = data.get('host', 'localhost')
    port = data.get('port', 9000)
    success, message, companies = fetch_companies_from_tally(host, port)
    return jsonify({'success': success, 'message': message, 'companies': companies})


@tally_bp.route('/synced-ledgers', methods=['GET'])
@login_required
def synced_ledgers():
    ledgers = get_synced_ledgers(current_user.email)
    result = [{'name': l[0], 'group': l[1], 'sync_date': str(l[2]) if l[2] else None} for l in ledgers]
    return jsonify({'success': True, 'ledgers': result})
