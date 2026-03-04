"""Voucher XML builders for all 8 Tally voucher types."""

from app.services.voucher_builders.sales import build_sales_xml
from app.services.voucher_builders.purchase import build_purchase_xml
from app.services.voucher_builders.journal import build_journal_xml
from app.services.voucher_builders.bank_payment import build_bank_payment_xml
from app.services.voucher_builders.bank_receipt import build_bank_receipt_xml
from app.services.voucher_builders.contra import build_contra_xml
from app.services.voucher_builders.debit_note import build_debit_note_xml
from app.services.voucher_builders.credit_note import build_credit_note_xml

_BUILDERS = {
    "sales": build_sales_xml,
    "purchase": build_purchase_xml,
    "journal": build_journal_xml,
    "bank_payment": build_bank_payment_xml,
    "bank_receipt": build_bank_receipt_xml,
    "contra": build_contra_xml,
    "debit_note": build_debit_note_xml,
    "credit_note": build_credit_note_xml,
}


def build_voucher_xml(voucher_type: str, row: dict, company_name: str) -> str:
    """Dispatch to the correct voucher builder."""
    vtype = voucher_type.lower().replace(" ", "_")
    builder = _BUILDERS.get(vtype)
    if not builder:
        raise ValueError(f"Unknown voucher type: {voucher_type}")
    return builder(row, company_name)
