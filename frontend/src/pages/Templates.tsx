import { useState, useEffect } from 'react';
import { toast } from 'sonner';
import { getTemplates, createTemplate, deleteTemplate } from '@/api/client';
import type { MappingTemplate } from '@/types';
import { VOUCHER_TYPES } from '@/types';
import { Trash2 } from 'lucide-react';

export default function Templates() {
    const [templates, setTemplates] = useState<MappingTemplate[]>([]);
    const [filter, setFilter] = useState('');

    const load = () => getTemplates(filter || undefined).then(setTemplates).catch(() => toast.error('Failed to load'));
    useEffect(() => { load(); }, [filter]);

    const handleDelete = async (id: string) => {
        if (!confirm('Delete this template?')) return;
        try { await deleteTemplate(id); toast.success('Deleted'); load(); }
        catch { toast.error('Failed'); }
    };

    return (
        <div className="mx-auto max-w-3xl">
            <h1 className="mb-6 text-2xl font-bold text-gray-800">Column Mapping Templates</h1>

            <div className="mb-4">
                <select value={filter} onChange={(e) => setFilter(e.target.value)}
                    className="rounded-lg border border-gray-300 px-4 py-2 text-sm focus:border-accent focus:outline-none">
                    <option value="">All Voucher Types</option>
                    {VOUCHER_TYPES.map(({ key, label }) => <option key={key} value={key}>{label}</option>)}
                </select>
            </div>

            <div className="space-y-3">
                {templates.map((t) => (
                    <div key={t.id} className="flex items-center justify-between rounded-xl border bg-white p-4 shadow-sm hover:shadow-md transition-all">
                        <div>
                            <h3 className="font-semibold text-gray-800">{t.name}</h3>
                            <p className="text-xs text-gray-500 capitalize">{t.voucher_type.replace('_', ' ')} • {Object.keys(t.mapping_json).length} fields mapped</p>
                        </div>
                        <button onClick={() => handleDelete(t.id)} className="rounded-lg border p-2 text-gray-500 hover:bg-red-50 hover:text-red-500">
                            <Trash2 size={16} />
                        </button>
                    </div>
                ))}
                {templates.length === 0 && (
                    <p className="rounded-xl border border-dashed p-8 text-center text-sm text-gray-400">
                        No templates yet. Save a column mapping during the upload wizard to create one.
                    </p>
                )}
            </div>
        </div>
    );
}
