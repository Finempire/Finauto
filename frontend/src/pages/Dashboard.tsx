import { useEffect, useState } from 'react';
import { NavLink } from 'react-router-dom';
import { getTallyConfigs, getTemplates } from '@/api/client';
import type { TallyConfig, MappingTemplate } from '@/types';
import { VOUCHER_TYPES } from '@/types';
import { Upload, Settings, FileText, ArrowRight, Wifi, WifiOff } from 'lucide-react';

export default function Dashboard() {
    const [configs, setConfigs] = useState<TallyConfig[]>([]);
    const [templates, setTemplates] = useState<MappingTemplate[]>([]);
    const [loadingConfigs, setLoadingConfigs] = useState(true);

    useEffect(() => {
        getTallyConfigs()
            .then(setConfigs)
            .catch(() => {})
            .finally(() => setLoadingConfigs(false));
        getTemplates().then(setTemplates).catch(() => {});
    }, []);

    const activeConfig = configs.find(
        (c) => c.id === localStorage.getItem('tally_config_id')
    ) || configs[0];

    return (
        <div className="mx-auto max-w-5xl space-y-8">
            {/* Header */}
            <div>
                <h1 className="text-3xl font-bold text-gray-800">Dashboard</h1>
                <p className="mt-1 text-sm text-gray-500">Upload Excel data directly into Tally ERP — fast, accurate, and automated</p>
            </div>

            {/* Status Cards */}
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
                {/* Tally Connection */}
                <div className={`rounded-xl border p-5 shadow-sm ${activeConfig ? 'border-green-200 bg-green-50' : 'border-red-200 bg-red-50'}`}>
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-xs font-semibold uppercase text-gray-500">Tally Server</p>
                            {loadingConfigs ? (
                                <p className="mt-1 text-sm text-gray-400">Loading...</p>
                            ) : activeConfig ? (
                                <>
                                    <p className="mt-1 font-semibold text-green-800">{activeConfig.label}</p>
                                    <p className="text-xs text-green-600">{activeConfig.host}:{activeConfig.port}</p>
                                </>
                            ) : (
                                <>
                                    <p className="mt-1 font-semibold text-red-700">Not configured</p>
                                    <NavLink to="/settings" className="text-xs text-red-600 underline">Add server →</NavLink>
                                </>
                            )}
                        </div>
                        {activeConfig ? (
                            <Wifi className="text-green-500" size={24} />
                        ) : (
                            <WifiOff className="text-red-400" size={24} />
                        )}
                    </div>
                </div>

                {/* Configs Count */}
                <div className="rounded-xl border border-blue-100 bg-blue-50 p-5 shadow-sm">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-xs font-semibold uppercase text-gray-500">Server Configs</p>
                            <p className="mt-1 text-3xl font-bold text-blue-700">{configs.length}</p>
                            <p className="text-xs text-blue-500">Tally connections</p>
                        </div>
                        <Settings className="text-blue-400" size={24} />
                    </div>
                </div>

                {/* Templates Count */}
                <div className="rounded-xl border border-purple-100 bg-purple-50 p-5 shadow-sm">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-xs font-semibold uppercase text-gray-500">Saved Templates</p>
                            <p className="mt-1 text-3xl font-bold text-purple-700">{templates.length}</p>
                            <p className="text-xs text-purple-500">Column mapping templates</p>
                        </div>
                        <FileText className="text-purple-400" size={24} />
                    </div>
                </div>
            </div>

            {/* Quick Start */}
            <div>
                <div className="mb-4 flex items-center justify-between">
                    <h2 className="text-lg font-bold text-gray-800">Quick Upload</h2>
                    <NavLink to="/upload" className="flex items-center gap-1 text-sm text-accent hover:underline">
                        Full wizard <ArrowRight size={14} />
                    </NavLink>
                </div>
                <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                    {VOUCHER_TYPES.map(({ key, label, icon, color }) => (
                        <NavLink
                            key={key}
                            to={`/upload?type=${key}`}
                            className={`flex flex-col items-center gap-2 rounded-xl bg-gradient-to-br ${color} p-5 text-white shadow-md transition-all hover:scale-105 hover:shadow-lg`}
                        >
                            <span className="text-3xl">{icon}</span>
                            <span className="text-xs font-semibold">{label}</span>
                        </NavLink>
                    ))}
                </div>
            </div>

            {/* How it works */}
            <div className="rounded-2xl border bg-white p-6 shadow-sm">
                <h2 className="mb-5 text-lg font-bold text-gray-800">How It Works</h2>
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-5">
                    {[
                        { icon: '1️⃣', title: 'Select Type', desc: 'Choose voucher type (Sales, Purchase, etc.)' },
                        { icon: '➡️', title: '', desc: '' },
                        { icon: '2️⃣', title: 'Upload Excel', desc: 'Drag & drop your spreadsheet' },
                        { icon: '➡️', title: '', desc: '' },
                        { icon: '3️⃣', title: 'Map Columns', desc: 'Auto-maps your columns to Tally fields' },
                    ].map((item, i) =>
                        item.title === '' ? (
                            <div key={i} className="hidden items-center justify-center sm:flex">
                                <div className="h-0.5 w-full bg-gray-200" />
                            </div>
                        ) : (
                            <div key={i} className="flex flex-col items-center gap-2 text-center">
                                <span className="text-2xl">{item.icon}</span>
                                <p className="text-sm font-semibold text-gray-700">{item.title}</p>
                                <p className="text-xs text-gray-500">{item.desc}</p>
                            </div>
                        )
                    )}
                </div>
                <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-5">
                    {[
                        { icon: '4️⃣', title: 'Validate', desc: 'Preview errors before pushing' },
                        { icon: '➡️', title: '', desc: '' },
                        { icon: '5️⃣', title: 'Push to Tally', desc: 'Real-time streaming progress' },
                        { icon: '', title: '', desc: '' },
                        { icon: '✅', title: 'Done!', desc: 'Vouchers created in Tally ERP' },
                    ].map((item, i) =>
                        item.icon === '➡️' ? (
                            <div key={i} className="hidden items-center justify-center sm:flex">
                                <div className="h-0.5 w-full bg-gray-200" />
                            </div>
                        ) : item.icon === '' ? (
                            <div key={i} />
                        ) : (
                            <div key={i} className="flex flex-col items-center gap-2 text-center">
                                <span className="text-2xl">{item.icon}</span>
                                <p className="text-sm font-semibold text-gray-700">{item.title}</p>
                                <p className="text-xs text-gray-500">{item.desc}</p>
                            </div>
                        )
                    )}
                </div>
            </div>

            {/* Getting Started Alert (no configs) */}
            {!loadingConfigs && configs.length === 0 && (
                <div className="rounded-xl border border-amber-200 bg-amber-50 p-5">
                    <h3 className="font-semibold text-amber-800">⚡ Get started in 2 steps</h3>
                    <ol className="mt-2 space-y-1 text-sm text-amber-700 list-decimal list-inside">
                        <li>
                            <NavLink to="/settings" className="underline font-medium">Go to Tally Settings</NavLink>
                            {' '}and add your Tally server (host + port)
                        </li>
                        <li>
                            Come back and use the <NavLink to="/upload" className="underline font-medium">Upload Wizard</NavLink> to push your first Excel file
                        </li>
                    </ol>
                </div>
            )}

            {/* Quick Links */}
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
                <NavLink to="/upload" className="flex items-center gap-4 rounded-xl border bg-white p-5 shadow-sm transition-all hover:border-accent hover:shadow-md">
                    <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-accent/10 text-accent">
                        <Upload size={22} />
                    </div>
                    <div>
                        <p className="font-semibold text-gray-800">Upload Wizard</p>
                        <p className="text-xs text-gray-500">Import Excel → Tally</p>
                    </div>
                </NavLink>

                <NavLink to="/settings" className="flex items-center gap-4 rounded-xl border bg-white p-5 shadow-sm transition-all hover:border-accent hover:shadow-md">
                    <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-blue-50 text-blue-500">
                        <Settings size={22} />
                    </div>
                    <div>
                        <p className="font-semibold text-gray-800">Tally Settings</p>
                        <p className="text-xs text-gray-500">Manage server configs</p>
                    </div>
                </NavLink>

                <NavLink to="/templates" className="flex items-center gap-4 rounded-xl border bg-white p-5 shadow-sm transition-all hover:border-accent hover:shadow-md">
                    <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-purple-50 text-purple-500">
                        <FileText size={22} />
                    </div>
                    <div>
                        <p className="font-semibold text-gray-800">Templates</p>
                        <p className="text-xs text-gray-500">Saved column mappings</p>
                    </div>
                </NavLink>
            </div>
        </div>
    );
}
