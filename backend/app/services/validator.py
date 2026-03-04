import re
from datetime import datetime

# Required fields per voucher type
REQUIRED_FIELDS: dict[str, list[str]] = {
    "sales": ["date", "party_name", "sales_ledger", "amount"],
    "purchase": ["date", "party_name", "purchase_ledger", "amount"],
    "bank_payment": ["date", "bank_ledger", "party_ledger", "amount"],
    "bank_receipt": ["date", "bank_ledger", "party_ledger", "amount"],
    "journal": ["date", "dr_ledger", "cr_ledger", "amount"],
    "contra": ["date", "from_account", "to_account", "amount"],
    "debit_note": ["date", "party_name", "amount"],
    "credit_note": ["date", "party_name", "amount"],
}

DATE_FORMATS = ["%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%d.%m.%Y", "%m/%d/%Y"]


def _parse_date(value: str) -> bool:
    """Try to parse a date string against known formats."""
    if not value:
        return False
    value = str(value).strip()
    for fmt in DATE_FORMATS:
        try:
            datetime.strptime(value, fmt)
            return True
        except ValueError:
            continue
    return False


def _is_positive_number(value) -> bool:
    """Check if value is a positive number."""
    if value is None:
        return False
    try:
        num = float(str(value).replace(",", "").strip())
        return num > 0
    except (ValueError, TypeError):
        return False


def validate_rows(
    rows: list[dict],
    mapping: dict[str, str],
    voucher_type: str,
) -> tuple[list[dict], int]:
    """
    Validate all rows against the mapping and voucher type rules.
    Returns (list_of_errors, valid_count).
    Each error: {"row": int, "field": str, "message": str}
    """
    vtype = voucher_type.lower().replace(" ", "_")
    required = REQUIRED_FIELDS.get(vtype, ["date", "amount"])

    # Build reverse mapping: tally_field -> excel_column
    reverse_map: dict[str, str] = {v: k for k, v in mapping.items()}

    errors: list[dict] = []
    valid_count = 0

    for i, row in enumerate(rows, start=1):
        row_errors: list[dict] = []

        for field in required:
            excel_col = reverse_map.get(field)
            if not excel_col:
                row_errors.append({
                    "row": i,
                    "field": field,
                    "message": f"Required field '{field}' is not mapped to any column",
                })
                continue

            value = row.get(excel_col)

            if value is None or str(value).strip() == "":
                row_errors.append({
                    "row": i,
                    "field": field,
                    "message": f"'{field}' is empty",
                })
            elif field == "date" and not _parse_date(str(value)):
                row_errors.append({
                    "row": i,
                    "field": field,
                    "message": f"Invalid date format: '{value}'. Use DD/MM/YYYY, YYYY-MM-DD, or DD-MM-YYYY.",
                })
            elif field == "amount" and not _is_positive_number(value):
                row_errors.append({
                    "row": i,
                    "field": field,
                    "message": f"Amount must be a positive number. Got: '{value}'",
                })

        if row_errors:
            errors.extend(row_errors)
        else:
            valid_count += 1

    return errors, valid_count
