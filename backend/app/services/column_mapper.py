import re

# Keyword -> Tally field mapping
KEYWORD_MAP: dict[str, str] = {
    "date": "date",
    "dt": "date",
    "voucher date": "date",
    "party": "party_name",
    "party name": "party_name",
    "customer": "party_name",
    "vendor": "party_name",
    "supplier": "party_name",
    "amount": "amount",
    "amt": "amount",
    "total": "amount",
    "value": "amount",
    "narration": "narration",
    "description": "narration",
    "particulars": "narration",
    "remarks": "narration",
    "ref": "ref_no",
    "reference": "ref_no",
    "ref no": "ref_no",
    "reference no": "ref_no",
    "bill": "bill_no",
    "bill no": "bill_no",
    "invoice": "bill_no",
    "invoice no": "bill_no",
    "cheque": "cheque_no",
    "cheque no": "cheque_no",
    "chq": "cheque_no",
    "bank": "bank_ledger",
    "bank ledger": "bank_ledger",
    "bank account": "bank_ledger",
    "sales": "sales_ledger",
    "sales ledger": "sales_ledger",
    "sales account": "sales_ledger",
    "purchase": "purchase_ledger",
    "purchase ledger": "purchase_ledger",
    "purchase account": "purchase_ledger",
    "party ledger": "party_ledger",
    "debit": "dr_ledger",
    "dr": "dr_ledger",
    "debit ledger": "dr_ledger",
    "credit": "cr_ledger",
    "cr": "cr_ledger",
    "credit ledger": "cr_ledger",
    "from": "from_account",
    "from account": "from_account",
    "to": "to_account",
    "to account": "to_account",
    "original ref": "original_voucher_ref",
    "original voucher": "original_voucher_ref",
}


def _normalize(header: str) -> str:
    """Lowercase, strip spaces, remove special chars."""
    cleaned = re.sub(r"[^a-z0-9\s]", "", header.lower().strip())
    return re.sub(r"\s+", " ", cleaned).strip()


def suggest_mapping(headers: list[str]) -> dict[str, str]:
    """Given Excel headers, suggest best Tally field mapping for each."""
    mapping: dict[str, str] = {}
    used_fields: set[str] = set()

    for header in headers:
        normalized = _normalize(header)
        matched_field = None

        # Try exact match
        if normalized in KEYWORD_MAP:
            matched_field = KEYWORD_MAP[normalized]
        else:
            # Try partial match
            for keyword, field in KEYWORD_MAP.items():
                if keyword in normalized or normalized in keyword:
                    matched_field = field
                    break

        if matched_field and matched_field not in used_fields:
            mapping[header] = matched_field
            used_fields.add(matched_field)

    return mapping
