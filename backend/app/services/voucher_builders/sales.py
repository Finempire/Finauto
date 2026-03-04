from lxml import etree


def build_sales_xml(row: dict, company_name: str) -> str:
    """Build Tally XML for a Sales voucher."""
    date = row.get("date", "")
    party = row.get("party_name", "")
    sales_ledger = row.get("sales_ledger", "Sales Account")
    amount = row.get("amount", "0")
    narration = row.get("narration", "")
    ref_no = row.get("ref_no", "")

    # Tally date format: YYYYMMDD
    tally_date = _format_date(date)

    envelope = etree.Element("ENVELOPE")
    header = etree.SubElement(envelope, "HEADER")
    etree.SubElement(header, "TALLYREQUEST").text = "Import Data"

    body = etree.SubElement(envelope, "BODY")
    import_data = etree.SubElement(body, "IMPORTDATA")
    request_desc = etree.SubElement(import_data, "REQUESTDESC")
    report_name = etree.SubElement(request_desc, "REPORTNAME").text = "Vouchers"
    static_vars = etree.SubElement(request_desc, "STATICVARIABLES")
    etree.SubElement(static_vars, "SVCURRENTCOMPANY").text = company_name

    request_data = etree.SubElement(import_data, "REQUESTDATA")
    tallymsg = etree.SubElement(request_data, "TALLYMESSAGE", xmlns_UDF="TallyUDF")
    voucher = etree.SubElement(tallymsg, "VOUCHER", VCHTYPE="Sales", ACTION="Create")
    etree.SubElement(voucher, "DATE").text = tally_date
    etree.SubElement(voucher, "VOUCHERTYPENAME").text = "Sales"
    etree.SubElement(voucher, "PARTYLEDGERNAME").text = party
    etree.SubElement(voucher, "NARRATION").text = narration
    if ref_no:
        etree.SubElement(voucher, "REFERENCE").text = ref_no

    # Debit: Party
    allledger1 = etree.SubElement(voucher, "ALLLEDGERENTRIES.LIST")
    etree.SubElement(allledger1, "LEDGERNAME").text = party
    etree.SubElement(allledger1, "ISDEEMEDPOSITIVE").text = "Yes"
    etree.SubElement(allledger1, "AMOUNT").text = f"-{amount}"

    # Credit: Sales Ledger
    allledger2 = etree.SubElement(voucher, "ALLLEDGERENTRIES.LIST")
    etree.SubElement(allledger2, "LEDGERNAME").text = sales_ledger
    etree.SubElement(allledger2, "ISDEEMEDPOSITIVE").text = "No"
    etree.SubElement(allledger2, "AMOUNT").text = amount

    return etree.tostring(envelope, pretty_print=True, xml_declaration=True, encoding="unicode")


def _format_date(date_str: str) -> str:
    """Convert common date formats to YYYYMMDD for Tally."""
    from datetime import datetime
    date_str = str(date_str).strip()
    for fmt in ["%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%d.%m.%Y", "%m/%d/%Y"]:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime("%Y%m%d")
        except ValueError:
            continue
    return date_str.replace("-", "").replace("/", "")
