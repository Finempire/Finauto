import { useState, useCallback, useRef } from 'react';
import { toast } from 'sonner';
import { parseFile, validateFile } from '@/api/client';
import { VOUCHER_TYPES, TALLY_FIELDS } from '@/types';
import type { ParseResponse, ValidateResponse, PushEvent } from '@/types';

const STEPS = ['Voucher Type', 'Upload File', 'Map Columns', 'Preview', 'Push to Tally'];

export default function UploadWizard() {
    const [step, setStep] = useState(0);
    const [voucherType, setVoucherType] = useState('');
    const [file, setFile] = useState<File | null>(null);
    const [parseResult, setParseResult] = useState<ParseResponse | null>(null);
    const [mapping, setMapping] = useState<Record<string, string>>({});
    const [validation, setValidation] = useState<ValidateResponse | null>(null);
    const [pushEvents, setPushEvents] = useState<PushEvent[]>([]);
    const [pushing, setPushing] = useState(false);
    const [loading, setLoading] = useState(false);
    const fileRef = useRef<HTMLInputElement>(null);

    // Step 1: Select voucher type
    const selectType = (key: string) => { setVoucherType(key); setStep(1); };

    // Step 2: Upload file
    const handleFile = useCallback(async (f: File) => {
        setFile(f);
        setLoading(true);
        try {
            const res = await parseFile(f);
            setParseResult(res);
            setMapping(res.suggested_mapping);
            setStep(2);
        } catch (err: any) {
            toast.error(err.response?.data?.detail || 'Failed to parse file');
        } finally {
            setLoading(false);
        }
    }, []);

    const onDrop = (e: React.DragEvent) => {
        e.preventDefault();
        const f = e.dataTransfer.files[0];
        if (f) handleFile(f);
    };

    // Step 3 -> 4: Validate
    const handleValidate = async () => {
        if (!file) return;
        setLoading(true);
        try {
            const res = await validateFile(file, mapping, voucherType);
            setValidation(res);
            setStep(3);
        } catch (err: any) {
            toast.error(err.response?.data?.detail || 'Validation failed');
        } finally {
            setLoading(false);
        }
    };

    // Step 5: Push via SSE
    const handlePush = () => {
        if (!file) return;
        setPushing(true);
        setPushEvents([]);
        setStep(4);

        const fd = new FormData();
        fd.append('file', file);
        fd.append('mapping', JSON.stringify(mapping));
        fd.append('voucher_type', voucherType);
        fd.append('tally_config_id', localStorage.getItem('tally_config_id') || '');
        fd.append('skip_errors', 'true');

        const token = localStorage.getItem('token');
        fetch('/api/upload/push', {
            method: 'POST',
            headers: token ? { Authorization: `Bearer ${token}` } : {},
            body: fd,
        }).then((resp) => {
            const reader = resp.body?.getReader();
            const decoder = new TextDecoder();
            const read = (): void => {
                reader?.read().then(({ done, value }) => {
                    if (done) { setPushing(false); return; }
                    const text = decoder.decode(value);
                    const lines = text.split('\n').filter((l) => l.startsWith('data: '));
                    for (const line of lines) {
                        try {
                            const event: PushEvent = JSON.parse(line.slice(6));
                            setPushEvents((prev) => [...prev, event]);
                            if (event.done) setPushing(false);
                        } catch { }
                    }
                    read();
                });
            };
            read();
        }).catch(() => { setPushing(false); toast.error('Push failed'); });
    };

    const reset = () => {
        setStep(0); setVoucherType(''); setFile(null);
        setParseResult(null); setMapping({}); setValidation(null);
        setPushEvents([]); setPushing(false);
    };

    const tallyFields = TALLY_FIELDS[voucherType] || [];
    const successCount = pushEvents.filter((e) => e.status === 'success').length;
    const failCount = pushEvents.filter((e) => e.status === 'failed').length;
    const totalPushed = successCount + failCount;
    const totalRows = parseResult?.total_rows || 0;

    return (
        <div className="mx-auto max-w-4xl">
            {/* Step Indicator */}
            <div className="mb-8 flex items-center justify-between">
                {STEPS.map((label, i) => (
                    <div key={i} className="flex items-center gap-2">
                        <div className={`relative flex h-8 w-8 items-center justify-center rounded-full text-xs font-bold transition-all ${i === step ? 'bg-accent text-white step-active' : i < step ? 'bg-green-500 text-white' : 'bg-gray-200 text-gray-500'
                            }`}>
                            {i < step ? '✓' : i + 1}
                        </div>
                        <span className={`hidden text-xs font-medium sm:block ${i === step ? 'text-accent' : 'text-gray-400'}`}>{label}</span>
                        {i < STEPS.length - 1 && <div className={`mx-2 h-0.5 w-8 ${i < step ? 'bg-green-500' : 'bg-gray-200'}`} />}
                    </div>
                ))}
            </div>

            {/* Step 1: Voucher Type */}
            {step === 0 && (
                <div>
                    <h2 className="mb-6 text-2xl font-bold text-gray-800">Select Voucher Type</h2>
                    <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
                        {VOUCHER_TYPES.map(({ key, label, icon, color }) => (
                            <button key={key} onClick={() => selectType(key)}
                                className={`group flex flex-col items-center gap-3 rounded-xl bg-gradient-to-br ${color} p-6 text-white shadow-lg transition-all hover:scale-105 hover:shadow-xl`}>
                                <span className="text-3xl">{icon}</span>
                                <span className="text-sm font-semibold">{label}</span>
                            </button>
                        ))}
                    </div>
                </div>
            )}

            {/* Step 2: Upload File */}
            {step === 1 && (
                <div>
                    <h2 className="mb-6 text-2xl font-bold text-gray-800">Upload Excel File</h2>
                    <div onDrop={onDrop} onDragOver={(e) => e.preventDefault()}
                        className="flex flex-col items-center justify-center rounded-2xl border-2 border-dashed border-accent/40 bg-accent/5 p-16 transition-colors hover:border-accent cursor-pointer"
                        onClick={() => fileRef.current?.click()}>
                        <span className="mb-3 text-5xl">📂</span>
                        <p className="text-lg font-semibold text-gray-700">Drag & drop your Excel file here</p>
                        <p className="mt-1 text-sm text-gray-500">or click to browse — .xlsx, .xls only (max 10MB)</p>
                        <input ref={fileRef} type="file" accept=".xlsx,.xls" className="hidden"
                            onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])} />
                    </div>
                    {loading && <div className="mt-4 flex items-center justify-center gap-2 text-accent">
                        <span className="h-5 w-5 animate-spin rounded-full border-2 border-accent border-t-transparent" /> Parsing file...
                    </div>}
                </div>
            )}

            {/* Step 3: Map Columns */}
            {step === 2 && parseResult && (
                <div>
                    <h2 className="mb-2 text-2xl font-bold text-gray-800">Map Columns</h2>
                    <p className="mb-6 text-sm text-gray-500">{parseResult.total_rows} rows found. Map your Excel columns to Tally fields.</p>
                    <div className="rounded-xl border bg-white shadow-sm">
                        <div className="grid grid-cols-2 gap-4 border-b bg-gray-50 px-6 py-3 text-xs font-semibold uppercase text-gray-500">
                            <span>Excel Column</span><span>Tally Field</span>
                        </div>
                        {parseResult.headers.map((header) => (
                            <div key={header} className="grid grid-cols-2 gap-4 border-b px-6 py-3 last:border-0">
                                <span className="text-sm font-medium text-gray-700">{header}</span>
                                <select value={mapping[header] || ''} onChange={(e) => setMapping({ ...mapping, [header]: e.target.value })}
                                    className="rounded-lg border border-gray-300 px-3 py-1.5 text-sm focus:border-accent focus:outline-none">
                                    <option value="">— Skip —</option>
                                    {tallyFields.map((f) => <option key={f} value={f}>{f}</option>)}
                                </select>
                            </div>
                        ))}
                    </div>
                    <div className="mt-6 flex gap-3">
                        <button onClick={() => setStep(1)} className="rounded-lg border border-gray-300 px-6 py-2.5 text-sm font-medium text-gray-700 hover:bg-gray-50">Back</button>
                        <button onClick={handleValidate} disabled={loading}
                            className="rounded-lg bg-accent px-6 py-2.5 text-sm font-semibold text-white shadow-md hover:bg-accent-dark disabled:opacity-60">
                            {loading ? 'Validating...' : 'Validate & Preview'}
                        </button>
                    </div>
                </div>
            )}

            {/* Step 4: Preview */}
            {step === 3 && validation && (
                <div>
                    <h2 className="mb-2 text-2xl font-bold text-gray-800">Preview & Validate</h2>
                    <div className="mb-4 flex gap-4">
                        <div className="rounded-lg bg-green-50 px-4 py-2 text-sm"><span className="font-bold text-green-700">{validation.valid_rows}</span> valid</div>
                        <div className="rounded-lg bg-red-50 px-4 py-2 text-sm"><span className="font-bold text-red-700">{validation.error_rows}</span> errors</div>
                        <div className="rounded-lg bg-gray-100 px-4 py-2 text-sm"><span className="font-bold text-gray-700">{validation.total_rows}</span> total</div>
                    </div>
                    {validation.errors.length > 0 && (
                        <div className="mb-4 max-h-48 overflow-auto rounded-lg border border-red-200 bg-red-50 p-4">
                            {validation.errors.slice(0, 20).map((err, i) => (
                                <p key={i} className="text-xs text-red-700">Row {err.row}: <strong>{err.field}</strong> — {err.message}</p>
                            ))}
                            {validation.errors.length > 20 && <p className="mt-2 text-xs text-red-500">...and {validation.errors.length - 20} more</p>}
                        </div>
                    )}
                    <div className="overflow-auto rounded-lg border bg-white shadow-sm">
                        <table className="w-full text-left text-xs">
                            <thead className="bg-gray-50"><tr>{parseResult?.headers.map((h) => <th key={h} className="px-3 py-2 font-semibold text-gray-500">{h}</th>)}</tr></thead>
                            <tbody>{validation.preview.slice(0, 50).map((row, i) => (
                                <tr key={i} className="border-t hover:bg-gray-50">{parseResult?.headers.map((h) => <td key={h} className="px-3 py-1.5 text-gray-700">{String(row[h] ?? '')}</td>)}</tr>
                            ))}</tbody>
                        </table>
                    </div>
                    <div className="mt-6 flex gap-3">
                        <button onClick={() => setStep(2)} className="rounded-lg border border-gray-300 px-6 py-2.5 text-sm font-medium text-gray-700 hover:bg-gray-50">Back</button>
                        <button onClick={handlePush} className="rounded-lg bg-green-600 px-6 py-2.5 text-sm font-semibold text-white shadow-md hover:bg-green-700">
                            🚀 Push to Tally
                        </button>
                    </div>
                </div>
            )}

            {/* Step 5: Push Progress */}
            {step === 4 && (
                <div>
                    <h2 className="mb-6 text-2xl font-bold text-gray-800">Pushing to Tally</h2>
                    {/* Progress Bar */}
                    <div className="mb-4">
                        <div className="flex justify-between text-sm text-gray-600 mb-1">
                            <span>{totalPushed} / {totalRows} rows</span>
                            <span className="font-medium">{totalRows > 0 ? Math.round((totalPushed / totalRows) * 100) : 0}%</span>
                        </div>
                        <div className="h-3 rounded-full bg-gray-200 overflow-hidden">
                            <div className="h-full rounded-full bg-gradient-to-r from-accent to-green-500 transition-all duration-300"
                                style={{ width: `${totalRows > 0 ? (totalPushed / totalRows) * 100 : 0}%` }} />
                        </div>
                    </div>
                    <div className="flex gap-4 mb-4">
                        <div className="rounded-lg bg-green-50 px-4 py-2 text-sm font-bold text-green-700">✓ {successCount}</div>
                        <div className="rounded-lg bg-red-50 px-4 py-2 text-sm font-bold text-red-700">✗ {failCount}</div>
                    </div>
                    {/* Live Log */}
                    <div className="max-h-64 overflow-auto rounded-lg border bg-gray-900 p-4 font-mono text-xs">
                        {pushEvents.map((ev, i) => (
                            <div key={i} className={ev.done ? 'text-yellow-400 font-bold mt-2' : ev.status === 'success' ? 'text-green-400' : 'text-red-400'}>
                                {ev.done ? `✅ Done — ${ev.success} success, ${ev.failed} failed` :
                                    `Row ${ev.row}: ${ev.status === 'success' ? `✓ ${ev.ref || 'OK'}` : `✗ ${ev.error}`}`}
                            </div>
                        ))}
                        {pushing && <div className="mt-1 text-accent animate-pulse">Processing...</div>}
                    </div>
                    {!pushing && pushEvents.some((e) => e.done) && (
                        <button onClick={reset} className="mt-6 rounded-lg bg-accent px-6 py-2.5 text-sm font-semibold text-white shadow-md hover:bg-accent-dark">
                            Upload Another File
                        </button>
                    )}
                </div>
            )}
        </div>
    );
}
