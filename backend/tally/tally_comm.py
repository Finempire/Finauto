"""Tally server communication utilities."""
import re
import xml.etree.ElementTree as ET
import requests
from html import escape
from datetime import datetime
from backend import db
from sqlalchemy import text


def normalize_tally_host(host):
    host = (host or '').strip()
    host = re.sub(r'^https?://', '', host, flags=re.IGNORECASE)
    host = host.split('/')[0]
    return host


def get_tally_host_candidates(host):
    normalized_host = normalize_tally_host(host)
    host_candidates = [normalized_host]
    local_aliases = {'localhost', '127.0.0.1', '0.0.0.0', '::1'}
    if normalized_host in local_aliases:
        docker_host_candidates = [
            'localhost', '127.0.0.1', 'host.docker.internal',
            'host.containers.internal', '172.17.0.1', '172.18.0.1'
        ]
        for candidate in docker_host_candidates:
            if candidate not in host_candidates:
                host_candidates.append(candidate)
    return [c for c in host_candidates if c]


def sanitize_tally_response(xml_text):
    if not xml_text:
        return xml_text
    cleaned = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F]', '', xml_text)
    cleaned = re.sub(r'&(?!amp;|lt;|gt;|apos;|quot;|#\d+;|#x[0-9A-Fa-f]+;)', '&amp;', cleaned)
    return cleaned


def _prepare_tally_payload(data):
    if isinstance(data, bytes):
        data = data.decode('utf-8', errors='replace')
    data = data.strip()
    if not data.startswith('<?xml'):
        data = '<?xml version="1.0" encoding="utf-8"?>\n' + data
    return data.encode('utf-8')


def post_to_tally_with_fallback(host, port, data, timeout):
    headers = {'Content-Type': 'application/xml; charset=utf-8'}
    payload = _prepare_tally_payload(data)
    host_candidates = get_tally_host_candidates(host)
    last_error = None
    for candidate in host_candidates:
        try:
            url = f"http://{candidate}:{port}"
            response = requests.post(url, data=payload, headers=headers, timeout=timeout)
            return response, candidate, host_candidates
        except requests.exceptions.ConnectionError as err:
            last_error = err
            continue
    if last_error:
        raise last_error
    raise requests.exceptions.ConnectionError(f"Unable to resolve a valid Tally host from '{host}'")


def check_tally_alive(host, port):
    host_candidates = get_tally_host_candidates(host)
    for candidate in host_candidates:
        try:
            url = f"http://{candidate}:{port}"
            requests.get(url, timeout=3)
            return True, f"Tally is reachable at {candidate}:{port}", candidate
        except Exception:
            continue
    return False, get_tally_connection_error_message(host, port, host_candidates), None


def get_tally_connection_error_message(host, port, host_candidates):
    troubleshooting = (
        "\n\n🔧 Troubleshooting Steps:\n"
        "1. Open Tally Prime → Press F1 (Help) → Settings → Connectivity\n"
        "2. Set Tally Prime Server to Yes\n"
        f"3. Verify the port is set to {port}\n"
        "4. Restart Tally Prime after changing settings\n"
        "5. Check that no firewall is blocking the port\n"
        "6. For remote machines, use the actual IP address instead of localhost"
    )
    if len(host_candidates) > 1:
        attempted = ', '.join(host_candidates)
        return f"Could not connect to Tally server at {host}:{port}. Tried hosts: {attempted}." + troubleshooting
    return f"Could not connect to Tally server at {host}:{port}." + troubleshooting


def sync_ledgers_from_tally(host, port, company_name, email):
    try:
        tally_request = f'''
        <ENVELOPE>
            <HEADER>
                <VERSION>1</VERSION>
                <TALLYREQUEST>Export</TALLYREQUEST>
                <TYPE>Collection</TYPE>
                <ID>List of Ledgers</ID>
            </HEADER>
            <BODY>
                <DESC>
                    <STATICVARIABLES>
                        <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
                        <SVCURRENTCOMPANY>{escape(company_name)}</SVCURRENTCOMPANY>
                    </STATICVARIABLES>
                    <TDL>
                        <TDLMESSAGE>
                            <COLLECTION NAME="MyLedgers" ISMODIFY="No" ISFIXED="No">
                                <TYPE>Ledger</TYPE>
                                <FETCH>Name, Parent</FETCH>
                            </COLLECTION>
                        </TDLMESSAGE>
                    </TDL>
                </DESC>
            </BODY>
        </ENVELOPE>
        '''
        response, _, _ = post_to_tally_with_fallback(host, port, tally_request, timeout=10)
        if response.status_code != 200:
            return False, f"Tally server returned error: {response.status_code}", 0
        try:
            cleaned = sanitize_tally_response(response.text)
            root = ET.fromstring(cleaned)
        except ET.ParseError as e:
            return False, f"Failed to parse Tally response: {str(e)}", 0

        ledgers = []
        for ledger_elem in root.findall('.//LEDGER'):
            name_elem = ledger_elem.find('.//NAME')
            parent_elem = ledger_elem.find('.//PARENT')
            if name_elem is not None and name_elem.text:
                ledger_name = name_elem.text.strip()
                ledger_group = parent_elem.text.strip() if parent_elem is not None and parent_elem.text else 'Unknown'
                ledgers.append((ledger_name, ledger_group))

        if not ledgers:
            return False, "No ledgers found in Tally response.", 0

        db.session.execute(text('DELETE FROM tally_synced_ledgers WHERE email = :email'), {'email': email})
        for ledger_name, ledger_group in ledgers:
            db.session.execute(text('''
                INSERT OR REPLACE INTO tally_synced_ledgers (email, ledger_name, ledger_group)
                VALUES (:email, :ledger_name, :ledger_group)
            '''), {'email': email, 'ledger_name': ledger_name, 'ledger_group': ledger_group})

        db.session.execute(text('''
            UPDATE tally_connection_settings SET last_sync_date = :sync_date WHERE email = :email
        '''), {'email': email, 'sync_date': datetime.now()})
        db.session.commit()
        return True, f"Successfully synced {len(ledgers)} ledgers from Tally", len(ledgers)

    except requests.exceptions.ConnectionError:
        return False, get_tally_connection_error_message(host, port, get_tally_host_candidates(host)), 0
    except requests.exceptions.Timeout:
        return False, "Connection to Tally server timed out.", 0
    except Exception as e:
        return False, f"Error syncing ledgers: {str(e)}", 0


def push_vouchers_to_tally(xml_data, host, port):
    try:
        response, _, _ = post_to_tally_with_fallback(host, port, xml_data, timeout=30)
        if response.status_code != 200:
            return False, f"Tally server returned error: {response.status_code}", 0

        vouchers_sent = xml_data.count('<TALLYMESSAGE')
        try:
            cleaned = sanitize_tally_response(response.text)
            root = ET.fromstring(cleaned)

            error_elem = root.find('.//ERROR')
            if error_elem is not None and error_elem.text and error_elem.text.strip():
                return False, f"Tally import error: {error_elem.text}", 0

            line_errors = root.findall('.//LINEERROR')
            if line_errors:
                details = [f"  {i}. {err.text}" for i, err in enumerate(line_errors[:5], 1)]
                msg = "Tally rejected vouchers with errors:\n" + "\n".join(details)
                if len(line_errors) > 5:
                    msg += f"\n  ... and {len(line_errors) - 5} more errors"
                return False, msg, 0

            created_elem = root.find('.//CREATED')
            if created_elem is not None and created_elem.text:
                try:
                    created_count = int(created_elem.text)
                    if created_count == 0:
                        return False, "Tally accepted the request but created 0 vouchers.", 0
                    elif created_count < vouchers_sent:
                        return False, f"Partial success: {created_count}/{vouchers_sent} vouchers created.", created_count
                    else:
                        return True, f"Successfully created {created_count} vouchers in Tally", created_count
                except ValueError:
                    pass

            last_vch = root.find('.//LASTVCHID')
            if last_vch is not None and last_vch.text:
                return True, f"Successfully pushed {vouchers_sent} vouchers to Tally", vouchers_sent

            import_result = root.find('.//IMPORTRESULT')
            if import_result is not None:
                status = import_result.find('.//STATUS')
                if status is not None and status.text:
                    if status.text.upper() == 'SUCCESS':
                        return True, f"Successfully pushed {vouchers_sent} vouchers to Tally", vouchers_sent
                    else:
                        return False, f"Tally import status: {status.text}", 0

            return False, "Uncertain result: Tally returned HTTP 200 but no confirmation.", 0
        except ET.ParseError as e:
            return False, f"Could not parse Tally response. Error: {str(e)}", 0

    except requests.exceptions.ConnectionError:
        return False, get_tally_connection_error_message(host, port, get_tally_host_candidates(host)), 0
    except requests.exceptions.Timeout:
        return False, "Connection to Tally server timed out.", 0
    except Exception as e:
        return False, f"Error pushing vouchers: {str(e)}", 0


def fetch_companies_from_tally(host, port):
    try:
        tally_request = '''
        <ENVELOPE>
            <HEADER>
                <VERSION>1</VERSION>
                <TALLYREQUEST>Export</TALLYREQUEST>
                <TYPE>Data</TYPE>
                <ID>ListOfCompanies</ID>
            </HEADER>
            <BODY>
                <DESC>
                    <STATICVARIABLES>
                        <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
                    </STATICVARIABLES>
                    <TDL>
                        <TDLMESSAGE>
                            <REPORT NAME="ListOfCompanies">
                                <FORMS>List</FORMS>
                                <FORM>List</FORM>
                            </REPORT>
                            <FORM NAME="List">
                                <TOPPARTS>List</TOPPARTS>
                                <PART>List</PART>
                            </FORM>
                            <PART NAME="List">
                                <TOPLINES>CompanyList</TOPLINES>
                                <LINE>CompanyList</LINE>
                                <REPEAT>CompanyList : Company</REPEAT>
                                <SCROLLED>Vertical</SCROLLED>
                            </PART>
                            <LINE NAME="CompanyList">
                                <FIELD>CompanyName</FIELD>
                            </LINE>
                            <FIELD NAME="CompanyName">
                                <SET>$Name</SET>
                            </FIELD>
                            <COLLECTION NAME="Company">
                                <TYPE>Company</TYPE>
                            </COLLECTION>
                        </TDLMESSAGE>
                    </TDL>
                </DESC>
            </BODY>
        </ENVELOPE>
        '''
        response, _, _ = post_to_tally_with_fallback(host, port, tally_request, timeout=10)
        if response.status_code != 200:
            return False, f"Tally server returned error: {response.status_code}", []

        try:
            cleaned = sanitize_tally_response(response.text)
            root = ET.fromstring(cleaned)
        except ET.ParseError as e:
            return False, f"Failed to parse Tally response: {str(e)}", []

        companies = []
        for elem in root.findall('.//COMPANYNAME'):
            if elem.text:
                companies.append(elem.text.strip())
        if not companies:
            for elem in root.findall('.//COMPANY'):
                name_elem = elem.find('.//NAME')
                if name_elem is not None and name_elem.text:
                    companies.append(name_elem.text.strip())
        if not companies:
            for elem in root.findall('.//NAME'):
                if elem.text and elem.text.strip():
                    companies.append(elem.text.strip())

        companies = list(dict.fromkeys(companies))
        if not companies:
            return False, "No companies found on Tally server.", []
        return True, f"Successfully detected {len(companies)} company(ies)", companies

    except requests.exceptions.ConnectionError:
        return False, get_tally_connection_error_message(host, port, get_tally_host_candidates(host)), []
    except requests.exceptions.Timeout:
        return False, "Connection to Tally server timed out.", []
    except Exception as e:
        return False, f"Error fetching companies: {str(e)}", []


def get_synced_ledgers(email):
    result = db.session.execute(text('''
        SELECT ledger_name, ledger_group, sync_date
        FROM tally_synced_ledgers WHERE email = :email ORDER BY ledger_name
    '''), {'email': email})
    return result.fetchall()
