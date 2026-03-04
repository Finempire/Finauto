from lxml import etree
from app.services.voucher_builders.sales import _format_date


def build_contra_xml(row: dict, company_name: str) -> str:
    """Build Tally XML for a Contra voucher."""
    date = row.get("date", "")
    from_account = row.get("from_account", "")
    to_account = row.get("to_account", "")
    amount = row.get("amount", "0")
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
    voucher = etree.SubElement(tallymsg, "VOUCHER", VCHTYPE="Contra", ACTION="Create")
    etree.SubElement(voucher, "DATE").text = tally_date
    etree.SubElement(voucher, "VOUCHERTYPENAME").text = "Contra"
    etree.SubElement(voucher, "NARRATION").text = narration

    e1 = etree.SubElement(voucher, "ALLLEDGERENTRIES.LIST")
    etree.SubElement(e1, "LEDGERNAME").text = to_account
    etree.SubElement(e1, "ISDEEMEDPOSITIVE").text = "Yes"
    etree.SubElement(e1, "AMOUNT").text = f"-{amount}"

    e2 = etree.SubElement(voucher, "ALLLEDGERENTRIES.LIST")
    etree.SubElement(e2, "LEDGERNAME").text = from_account
    etree.SubElement(e2, "ISDEEMEDPOSITIVE").text = "No"
    etree.SubElement(e2, "AMOUNT").text = amount

    return etree.tostring(envelope, pretty_print=True, xml_declaration=True, encoding="unicode")
