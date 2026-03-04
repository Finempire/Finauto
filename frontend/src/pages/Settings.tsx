import { useState, useEffect } from 'react';
import { toast } from 'sonner';
import { getTallyConfigs, createTallyConfig, deleteTallyConfig, pingTally } from '@/api/client';
import type { TallyConfig } from '@/types';
import { Plus, Trash2, Wifi, WifiOff } from 'lucide-react';

export default function Settings() {
    const [configs, setConfigs] = useState<TallyConfig[]>([]);
    const [showForm, setShowForm] = useState(false);
    const [label, setLabel] = useState('');
    const [host, setHost] = useState('localhost');
    const [port, setPort] = useState(9000);
    const [company, setCompany] = useState('');
    const [loading, setLoading] = useState(false);

    const load = () => getTallyConfigs().then(setConfigs).catch(() => toast.error('Failed to load configs'));

    useEffect(() => { load(); }, []);

    const handleCreate = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        try {
            await createTallyConfig({ label, host, port, company_name: company || null });
            toast.success('Config saved');
            setShowForm(false); setLabel(''); setHost('localhost'); setPort(9000); setCompany('');
            load();
        } catch { toast.error('Failed to save'); }
        finally { setLoading(false); }
    };

    const handleDelete = async (id: string) => {
        if (!confirm('Delete this config?')) return;
        try { await deleteTallyConfig(id); toast.success('Deleted'); load(); }
        catch { toast.error('Failed to delete'); }
    };

    const handlePing = async (c: TallyConfig) => {
        const res = await pingTally(c.host, c.port);
        if (res.reachable) toast.success(res.message);
        else toast.error(res.message);
    };

    const handleSelect = (id: string) => {
        localStorage.setItem('tally_config_id', id);
        toast.success('Active config updated');
    };

    const activeId = localStorage.getItem('tally_config_id');

    return (
        <div className="mx-auto max-w-3xl">
            <div className="mb-6 flex items-center justify-between">
                <h1 className="text-2xl font-bold text-gray-800">Tally Server Settings</h1>
                <button onClick={() => setShowForm(!showForm)}
                    className="flex items-center gap-2 rounded-lg bg-accent px-4 py-2 text-sm font-semibold text-white shadow-md hover:bg-accent-dark">
                    <Plus size={16} /> Add Config
                </button>
            </div>

            {showForm && (
                <form onSubmit={handleCreate} className="mb-6 rounded-xl border bg-white p-6 shadow-sm">
                    <div className="grid grid-cols-2 gap-4">
                        <div><label className="mb-1 block text-xs font-medium text-gray-600">Label</label>
                            <input value={label} onChange={(e) => setLabel(e.target.value)} required className="w-full rounded-lg border px-3 py-2 text-sm focus:border-accent focus:outline-none" placeholder="Main Office" /></div>
                        <div><label className="mb-1 block text-xs font-medium text-gray-600">Host</label>
                            <input value={host} onChange={(e) => setHost(e.target.value)} className="w-full rounded-lg border px-3 py-2 text-sm focus:border-accent focus:outline-none" /></div>
                        <div><label className="mb-1 block text-xs font-medium text-gray-600">Port</label>
                            <input type="number" value={port} onChange={(e) => setPort(+e.target.value)} className="w-full rounded-lg border px-3 py-2 text-sm focus:border-accent focus:outline-none" /></div>
                        <div><label className="mb-1 block text-xs font-medium text-gray-600">Company Name</label>
                            <input value={company} onChange={(e) => setCompany(e.target.value)} className="w-full rounded-lg border px-3 py-2 text-sm focus:border-accent focus:outline-none" placeholder="Optional" /></div>
                    </div>
                    <div className="mt-4 flex gap-2">
                        <button type="submit" disabled={loading} className="rounded-lg bg-accent px-4 py-2 text-sm font-semibold text-white hover:bg-accent-dark disabled:opacity-60">Save</button>
                        <button type="button" onClick={() => setShowForm(false)} className="rounded-lg border px-4 py-2 text-sm text-gray-600 hover:bg-gray-50">Cancel</button>
                    </div>
                </form>
            )}

            <div className="space-y-3">
                {configs.map((c) => (
                    <div key={c.id} className={`flex items-center justify-between rounded-xl border p-4 transition-all ${activeId === c.id ? 'border-accent bg-accent/5 shadow-md' : 'bg-white shadow-sm hover:shadow-md'}`}>
                        <div className="cursor-pointer flex-1" onClick={() => handleSelect(c.id)}>
                            <h3 className="font-semibold text-gray-800">{c.label}</h3>
                            <p className="text-xs text-gray-500">{c.host}:{c.port} {c.company_name ? `• ${c.company_name}` : ''}</p>
                        </div>
                        <div className="flex gap-2">
                            <button onClick={() => handlePing(c)} className="rounded-lg border p-2 text-gray-500 hover:bg-gray-50 hover:text-accent" title="Test connection"><Wifi size={16} /></button>
                            <button onClick={() => handleDelete(c.id)} className="rounded-lg border p-2 text-gray-500 hover:bg-red-50 hover:text-red-500" title="Delete"><Trash2 size={16} /></button>
                        </div>
                    </div>
                ))}
                {configs.length === 0 && <p className="rounded-xl border border-dashed p-8 text-center text-sm text-gray-400">No Tally configs yet. Add one above to get started.</p>}
            </div>
        </div>
    );
}
