export interface User {
    id: string;
    email: string;
    full_name: string | null;
    role: 'admin' | 'operator';
    is_active: boolean;
    created_at: string;
}

export interface TallyConfig {
    id: string;
    label: string;
    host: string;
    port: number;
    company_name: string | null;
    created_at: string;
}

export interface MappingTemplate {
    id: string;
    name: string;
    voucher_type: string;
    mapping_json: Record<string, string>;
    created_at: string;
}

export interface ParseResponse {
    headers: string[];
    preview_rows: Record<string, any>[];
    suggested_mapping: Record<string, string>;
    total_rows: number;
}

export interface ValidateResponse {
    total_rows: number;
    valid_rows: number;
    error_rows: number;
    errors: { row: number; field: string; message: string }[];
    preview: Record<string, any>[];
}

export interface PushEvent {
    row?: number;
    status?: 'success' | 'failed';
    ref?: string;
    error?: string;
    done?: boolean;
    success?: number;
    failed?: number;
}

export const VOUCHER_TYPES = [
    { key: 'sales', label: 'Sales', icon: '📦', color: 'from-blue-500 to-blue-600' },
    { key: 'purchase', label: 'Purchase', icon: '🛒', color: 'from-emerald-500 to-emerald-600' },
    { key: 'bank_payment', label: 'Bank Payment', icon: '💳', color: 'from-red-500 to-red-600' },
    { key: 'bank_receipt', label: 'Bank Receipt', icon: '💰', color: 'from-green-500 to-green-600' },
    { key: 'journal', label: 'Journal', icon: '📝', color: 'from-purple-500 to-purple-600' },
    { key: 'contra', label: 'Contra', icon: '🔄', color: 'from-orange-500 to-orange-600' },
    { key: 'debit_note', label: 'Debit Note', icon: '📋', color: 'from-pink-500 to-pink-600' },
    { key: 'credit_note', label: 'Credit Note', icon: '📄', color: 'from-teal-500 to-teal-600' },
] as const;

export const TALLY_FIELDS: Record<string, string[]> = {
    sales: ['date', 'party_name', 'sales_ledger', 'amount', 'narration', 'ref_no'],
    purchase: ['date', 'party_name', 'purchase_ledger', 'amount', 'bill_no', 'narration'],
    bank_payment: ['date', 'bank_ledger', 'party_ledger', 'amount', 'cheque_no', 'narration'],
    bank_receipt: ['date', 'bank_ledger', 'party_ledger', 'amount', 'ref_no', 'narration'],
    journal: ['date', 'dr_ledger', 'cr_ledger', 'amount', 'narration'],
    contra: ['date', 'from_account', 'to_account', 'amount', 'narration'],
    debit_note: ['date', 'party_name', 'amount', 'original_voucher_ref', 'narration'],
    credit_note: ['date', 'party_name', 'amount', 'original_voucher_ref', 'narration'],
};
