from lxml import etree
from app.services.voucher_builders.sales import _format_date


def build_bank_payment_xml(row: dict, company_name: str) -> str:
    """Build Tally XML for a Bank Payment voucher."""
    date = row.get("date", "")
    bank_ledger = row.get("bank_ledger", "")
    party_ledger = row.get("party_ledger", "")
    amount = row.get("amount", "0")
    cheque_no = row.get("cheque_no", "")
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
    voucher = etree.SubElement(tallymsg, "VOUCHER", VCHTYPE="Payment", ACTION="Create")
    etree.SubElement(voucher, "DATE").text = tally_date
    etree.SubElement(voucher, "VOUCHERTYPENAME").text = "Payment"
    etree.SubElement(voucher, "NARRATION").text = narration

    # Debit: Party (payment goes to)
    e1 = etree.SubElement(voucher, "ALLLEDGERENTRIES.LIST")
    etree.SubElement(e1, "LEDGERNAME").text = party_ledger
    etree.SubElement(e1, "ISDEEMEDPOSITIVE").text = "Yes"
    etree.SubElement(e1, "AMOUNT").text = f"-{amount}"

    # Credit: Bank
    e2 = etree.SubElement(voucher, "ALLLEDGERENTRIES.LIST")
    etree.SubElement(e2, "LEDGERNAME").text = bank_ledger
    etree.SubElement(e2, "ISDEEMEDPOSITIVE").text = "No"
    etree.SubElement(e2, "AMOUNT").text = amount

    return etree.tostring(envelope, pretty_print=True, xml_declaration=True, encoding="unicode")
