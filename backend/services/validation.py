import pandas as pd
from typing import List, Tuple, Dict, Any

class ValidationError(Exception):
    """Exception raised for errors in the imported data."""
    def __init__(self, message, errors=None):
        super().__init__(message)
        self.errors = errors or []

class ValidationService:
    @staticmethod
    def validate_bank_upload(df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """Validate an uploaded bank statement dataframe."""
        errors = []
        required_cols = ['Date', 'Narration', 'Debit', 'Credit']
        
        # Check for missing columns (case insensitive)
        df_cols_upper = [str(c).upper().strip() for c in df.columns]
        for req in required_cols:
            if req.upper() not in df_cols_upper:
                errors.append(f"Missing mandatory column: {req}")
                
        if errors:
            return False, errors
            
        # Rename columns to standard case if they exist
        rename_map = {}
        for c in df.columns:
            for req in required_cols:
                if str(c).upper().strip() == req.upper():
                    rename_map[c] = req
        df.rename(columns=rename_map, inplace=True)
        
        return True, []

    @staticmethod
    def validate_bank_mapping(rows: List[Dict[str, Any]]) -> Tuple[bool, List[str]]:
        """Validate mapped rows before XML generation."""
        errors = []
        for idx, row in enumerate(rows):
            # Check date format
            date_val = str(row.get('Date', '')).strip()
            if not date_val:
                errors.append(f"Row {idx+1}: Missing Date")
                
            # Check amounts
            debit = float(row.get('Debit') or 0)
            credit = float(row.get('Credit') or 0)
            if debit <= 0 and credit <= 0:
                errors.append(f"Row {idx+1}: Both Debit and Credit are zero or empty")
            if debit > 0 and credit > 0:
                errors.append(f"Row {idx+1}: Both Debit and Credit have values")
                
            # Check mapped ledger
            mapped = str(row.get('Mapped Ledger', '')).strip()
            if not mapped:
                errors.append(f"Row {idx+1} ('{row.get('Narration', '')}'): Ledger not mapped")
                
        return len(errors) == 0, errors

    @staticmethod
    def validate_journal_upload(df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """Validate journal template dataframe."""
        if len(df.columns) < 2:
            return False, ["Journal upload requires at least 2 columns"]
        return True, []
