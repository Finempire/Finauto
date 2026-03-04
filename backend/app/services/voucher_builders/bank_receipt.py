from lxml import etree
from app.services.voucher_builders.sales import _format_date


def build_bank_receipt_xml(row: dict, company_name: str) -> str:
    """Build Tally XML for a Bank Receipt voucher."""
    date = row.get("date", "")
    bank_ledger = row.get("bank_ledger", "")
    party_ledger = row.get("party_ledger", "")
    amount = row.get("amount", "0")
    ref_no = row.get("ref_no", "")
    narration = row.get("narration", "")
    tally_date = _format_date(date)

    envelope = etree.Element("ENVELOPE")
    header = etree.SubElement(envelope, "HEADER")
    etree.SubElement(header, "TALLYREQUEST").text = "Import Data"
    body = etree.SubElement(envelope, "BODY")
    import_data = etree.SubElement(body, "IMPORTDATA")
    request_desc = etree.SubElement(import_data, "REQUESTDESC")
    etree.SubElement(request_desc, "REPORTNAME").text = "Vouchers"
    static_vars = etree.SubElement(request_desc, "STATICVARIABLES")
    etree.SubElement(static_vars, "SVCURRENTCOMPANY").text = company_name
    request_data = etree.SubElement(import_data, "REQUESTDATA")
    tallymsg = etree.SubElement(request_data, "TALLYMESSAGE", xmlns_UDF="TallyUDF")
    voucher = etree.SubElement(tallymsg, "VOUCHER", VCHTYPE="Receipt", ACTION="Create")
    etree.SubElement(voucher, "DATE").text = tally_date
    etree.SubElement(voucher, "VOUCHERTYPENAME").text = "Receipt"
    etree.SubElement(voucher, "NARRATION").text = narration

    # Debit: Bank
    e1 = etree.SubElement(voucher, "ALLLEDGERENTRIES.LIST")
    etree.SubElement(e1, "LEDGERNAME").text = bank_ledger
    etree.SubElement(e1, "ISDEEMEDPOSITIVE").text = "Yes"
    etree.SubElement(e1, "AMOUNT").text = f"-{amount}"

    # Credit: Party
    e2 = etree.SubElement(voucher, "ALLLEDGERENTRIES.LIST")
    etree.SubElement(e2, "LEDGERNAME").text = party_ledger
    etree.SubElement(e2, "ISDEEMEDPOSITIVE").text = "No"
    etree.SubElement(e2, "AMOUNT").text = amount

    return etree.tostring(envelope, pretty_print=True, xml_declaration=True, encoding="unicode")
