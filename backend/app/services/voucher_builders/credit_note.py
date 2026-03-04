from lxml import etree
from app.services.voucher_builders.sales import _format_date


def build_credit_note_xml(row: dict, company_name: str) -> str:
    """Build Tally XML for a Credit Note voucher."""
    date = row.get("date", "")
    party = row.get("party_name", "")
    amount = row.get("amount", "0")
    original_ref = row.get("original_voucher_ref", "")
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
    voucher = etree.SubElement(tallymsg, "VOUCHER", VCHTYPE="Credit Note", ACTION="Create")
    etree.SubElement(voucher, "DATE").text = tally_date
    etree.SubElement(voucher, "VOUCHERTYPENAME").text = "Credit Note"
    etree.SubElement(voucher, "PARTYLEDGERNAME").text = party
    etree.SubElement(voucher, "NARRATION").text = narration
    if original_ref:
        etree.SubElement(voucher, "REFERENCE").text = original_ref

    e1 = etree.SubElement(voucher, "ALLLEDGERENTRIES.LIST")
    etree.SubElement(e1, "LEDGERNAME").text = "Sales Account"
    etree.SubElement(e1, "ISDEEMEDPOSITIVE").text = "Yes"
    etree.SubElement(e1, "AMOUNT").text = f"-{amount}"

    e2 = etree.SubElement(voucher, "ALLLEDGERENTRIES.LIST")
    etree.SubElement(e2, "LEDGERNAME").text = party
    etree.SubElement(e2, "ISDEEMEDPOSITIVE").text = "No"
    etree.SubElement(e2, "AMOUNT").text = amount

    return etree.tostring(envelope, pretty_print=True, xml_declaration=True, encoding="unicode")
