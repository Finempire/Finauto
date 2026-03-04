import { Routes, Route, Navigate } from 'react-router-dom';
import { useState, useEffect } from 'react';
import { getMe } from '@/api/client';
import type { User } from '@/types';
import Sidebar from '@/components/Sidebar';
import Login from '@/pages/Login';
import UploadWizard from '@/pages/UploadWizard';
import Settings from '@/pages/Settings';
import Templates from '@/pages/Templates';
import Users from '@/pages/Users';

export default function App() {
    const [user, setUser] = useState<User | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const token = localStorage.getItem('token');
        if (!token) { setLoading(false); return; }
        getMe()
            .then(setUser)
            .catch(() => localStorage.removeItem('token'))
            .finally(() => setLoading(false));
    }, []);

    if (loading) {
        return (
            <div className="flex h-screen items-center justify-center">
                <div className="h-10 w-10 animate-spin rounded-full border-4 border-accent border-t-transparent" />
            </div>
        );
    }

    if (!user) {
        return <Login onLogin={setUser} />;
    }

    return (
        <div className="flex h-screen bg-gray-50">
            <Sidebar user={user} onLogout={() => { localStorage.removeItem('token'); setUser(null); }} />
            <main className="flex-1 overflow-auto p-6">
                <Routes>
                    <Route path="/" element={<UploadWizard />} />
                    <Route path="/settings" element={<Settings />} />
                    <Route path="/templates" element={<Templates />} />
                    <Route path="/admin/users" element={user.role === 'admin' ? <Users /> : <Navigate to="/" />} />
                    <Route path="*" element={<Navigate to="/" />} />
                </Routes>
            </main>
        </div>
    );
}
