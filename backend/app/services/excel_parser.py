import io

import pandas as pd


def parse_excel(file_bytes: bytes) -> tuple[list[str], list[dict]]:
    """Parse an Excel file from bytes and return (headers, rows_as_dicts)."""
    buffer = io.BytesIO(file_bytes)
    df = pd.read_excel(buffer, engine="openpyxl")

    # Clean column names
    df.columns = [str(col).strip() for col in df.columns]

    # Drop completely empty rows
    df = df.dropna(how="all").reset_index(drop=True)

    # Convert NaN to None for JSON compatibility
    df = df.where(df.notna(), None)

    headers = list(df.columns)
    rows = df.to_dict(orient="records")

    return headers, rows
