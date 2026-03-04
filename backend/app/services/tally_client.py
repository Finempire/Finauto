from typing import AsyncGenerator

import httpx
from lxml import etree

from app.models.tally_config import TallyConfig
from app.services.voucher_builders import build_voucher_xml


async def ping_tally(host: str, port: int) -> tuple[bool, str]:
    """Test if Tally is reachable at given host:port."""
    url = f"http://{host}:{port}"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(url)
            return True, f"Tally is reachable (status {resp.status_code})"
    except httpx.ConnectError:
        return False, f"Cannot connect to Tally at {host}:{port}"
    except httpx.TimeoutException:
        return False, f"Connection to {host}:{port} timed out"
    except Exception as e:
        return False, f"Error: {str(e)}"


async def fetch_companies(host: str, port: int) -> list[str]:
    """Fetch the list of companies from Tally."""
    url = f"http://{host}:{port}"
    xml_request = """<ENVELOPE>
    <HEADER><VERSION>1</VERSION><TALLYREQUEST>Export</TALLYREQUEST><TYPE>Collection</TYPE><ID>List of Companies</ID></HEADER>
    <BODY><DESC><STATICVARIABLES><SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT></STATICVARIABLES><TDL><TDLMESSAGE><COLLECTION NAME="List of Companies"><TYPE>Company</TYPE><FETCH>Name</FETCH></COLLECTION></TDLMESSAGE></TDL></DESC></BODY>
    </ENVELOPE>"""

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, content=xml_request, headers={"Content-Type": "text/xml"})
            root = etree.fromstring(resp.content)
            companies = [elem.text for elem in root.iter("NAME") if elem.text]
            return companies
    except Exception:
        return []


async def _push_single_voucher(
    client: httpx.AsyncClient,
    xml_str: str,
    host: str,
    port: int,
) -> tuple[bool, str]:
    """Push a single voucher XML to Tally, return (success, message)."""
    url = f"http://{host}:{port}"
    for attempt in range(2):  # retry once on timeout
        try:
            resp = await client.post(url, content=xml_str, headers={"Content-Type": "text/xml"}, timeout=10.0)
            body = resp.text

            if "<LINEERROR>" in body or "<ERRORS>" in body:
                root = etree.fromstring(resp.content)
                error_elem = root.find(".//LINEERROR")
                if error_elem is None:
                    error_elem = root.find(".//ERRORS")
                error_msg = error_elem.text if error_elem is not None and error_elem.text else "Unknown Tally error"
                return False, error_msg

            return True, "Success"
        except httpx.TimeoutException:
            if attempt == 0:
                continue
            return False, "Tally request timed out after retry"
        except Exception as e:
            return False, str(e)

    return False, "Unexpected error"


async def push_vouchers(
    rows: list[dict],
    mapping: dict[str, str],
    voucher_type: str,
    config: TallyConfig,
    skip_errors: bool,
) -> AsyncGenerator[dict, None]:
    """Push vouchers one-by-one and yield SSE events."""
    reverse_map = {v: k for k, v in mapping.items()}
    success_count = 0
    fail_count = 0

    async with httpx.AsyncClient() as client:
        for i, row in enumerate(rows, start=1):
            # Build mapped row
            mapped_row: dict = {}
            for tally_field, excel_col in reverse_map.items():
                value = row.get(excel_col)
                mapped_row[tally_field] = str(value) if value is not None else ""

            # Build XML
            try:
                xml_str = build_voucher_xml(voucher_type, mapped_row, config.company_name or "")
            except Exception as e:
                if skip_errors:
                    fail_count += 1
                    yield {"row": i, "status": "failed", "error": f"XML build error: {str(e)}"}
                    continue
                else:
                    fail_count += 1
                    yield {"row": i, "status": "failed", "error": f"XML build error: {str(e)}"}
                    continue

            # Push to Tally
            ok, message = await _push_single_voucher(client, xml_str, config.host, config.port)
            if ok:
                success_count += 1
                yield {"row": i, "status": "success", "ref": mapped_row.get("ref_no", "")}
            else:
                fail_count += 1
                yield {"row": i, "status": "failed", "error": message}

    yield {"done": True, "success": success_count, "failed": fail_count}
