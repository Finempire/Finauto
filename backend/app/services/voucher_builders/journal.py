from lxml import etree
from app.services.voucher_builders.sales import _format_date


def build_journal_xml(row: dict, company_name: str) -> str:
    """Build Tally XML for a Journal voucher."""
    date = row.get("date", "")
    dr_ledger = row.get("dr_ledger", "")
    cr_ledger = row.get("cr_ledger", "")
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
    voucher = etree.SubElement(tallymsg, "VOUCHER", VCHTYPE="Journal", ACTION="Create")
    etree.SubElement(voucher, "DATE").text = tally_date
    etree.SubElement(voucher, "VOUCHERTYPENAME").text = "Journal"
    etree.SubElement(voucher, "NARRATION").text = narration

    # Debit
    allledger1 = etree.SubElement(voucher, "ALLLEDGERENTRIES.LIST")
    etree.SubElement(allledger1, "LEDGERNAME").text = dr_ledger
    etree.SubElement(allledger1, "ISDEEMEDPOSITIVE").text = "Yes"
    etree.SubElement(allledger1, "AMOUNT").text = f"-{amount}"

    # Credit
    allledger2 = etree.SubElement(voucher, "ALLLEDGERENTRIES.LIST")
    etree.SubElement(allledger2, "LEDGERNAME").text = cr_ledger
    etree.SubElement(allledger2, "ISDEEMEDPOSITIVE").text = "No"
    etree.SubElement(allledger2, "AMOUNT").text = amount

    return etree.tostring(envelope, pretty_print=True, xml_declaration=True, encoding="unicode")
