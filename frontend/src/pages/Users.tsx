import { useState, useEffect } from 'react';
import { toast } from 'sonner';
import { getUsers, createUser, updateUser, deleteUser } from '@/api/client';
import type { User } from '@/types';
import { Plus, Trash2, UserCheck, UserX } from 'lucide-react';

export default function Users() {
    const [users, setUsers] = useState<User[]>([]);
    const [showForm, setShowForm] = useState(false);
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [fullName, setFullName] = useState('');
    const [role, setRole] = useState('operator');
    const [loading, setLoading] = useState(false);

    const load = () => getUsers().then(setUsers).catch(() => toast.error('Failed to load users'));
    useEffect(() => { load(); }, []);

    const handleCreate = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        try {
            await createUser({ email, password, full_name: fullName || null, role });
            toast.success('User created');
            setShowForm(false); setEmail(''); setPassword(''); setFullName(''); setRole('operator');
            load();
        } catch (err: any) { toast.error(err.response?.data?.detail || 'Failed'); }
        finally { setLoading(false); }
    };

    const toggleActive = async (u: User) => {
        try { await updateUser(u.id, { is_active: !u.is_active }); toast.success(`User ${u.is_active ? 'deactivated' : 'activated'}`); load(); }
        catch { toast.error('Failed'); }
    };

    const toggleRole = async (u: User) => {
        const newRole = u.role === 'admin' ? 'operator' : 'admin';
        try { await updateUser(u.id, { role: newRole }); toast.success(`Role changed to ${newRole}`); load(); }
        catch { toast.error('Failed'); }
    };

    const handleDelete = async (id: string) => {
        if (!confirm('Delete this user permanently?')) return;
        try { await deleteUser(id); toast.success('Deleted'); load(); }
        catch { toast.error('Failed'); }
    };

    return (
        <div className="mx-auto max-w-3xl">
            <div className="mb-6 flex items-center justify-between">
                <h1 className="text-2xl font-bold text-gray-800">User Management</h1>
                <button onClick={() => setShowForm(!showForm)}
                    className="flex items-center gap-2 rounded-lg bg-accent px-4 py-2 text-sm font-semibold text-white shadow-md hover:bg-accent-dark">
                    <Plus size={16} /> Add User
                </button>
            </div>

            {showForm && (
                <form onSubmit={handleCreate} className="mb-6 rounded-xl border bg-white p-6 shadow-sm">
                    <div className="grid grid-cols-2 gap-4">
                        <div><label className="mb-1 block text-xs font-medium text-gray-600">Email</label>
                            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required className="w-full rounded-lg border px-3 py-2 text-sm focus:border-accent focus:outline-none" /></div>
                        <div><label className="mb-1 block text-xs font-medium text-gray-600">Password</label>
                            <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required minLength={8} className="w-full rounded-lg border px-3 py-2 text-sm focus:border-accent focus:outline-none" /></div>
                        <div><label className="mb-1 block text-xs font-medium text-gray-600">Full Name</label>
                            <input value={fullName} onChange={(e) => setFullName(e.target.value)} className="w-full rounded-lg border px-3 py-2 text-sm focus:border-accent focus:outline-none" /></div>
                        <div><label className="mb-1 block text-xs font-medium text-gray-600">Role</label>
                            <select value={role} onChange={(e) => setRole(e.target.value)} className="w-full rounded-lg border px-3 py-2 text-sm focus:border-accent focus:outline-none">
                                <option value="operator">Operator</option><option value="admin">Admin</option>
                            </select></div>
                    </div>
                    <div className="mt-4 flex gap-2">
                        <button type="submit" disabled={loading} className="rounded-lg bg-accent px-4 py-2 text-sm font-semibold text-white hover:bg-accent-dark disabled:opacity-60">Create</button>
                        <button type="button" onClick={() => setShowForm(false)} className="rounded-lg border px-4 py-2 text-sm text-gray-600 hover:bg-gray-50">Cancel</button>
                    </div>
                </form>
            )}

            <div className="space-y-3">
                {users.map((u) => (
                    <div key={u.id} className={`flex items-center justify-between rounded-xl border p-4 transition-all ${u.is_active ? 'bg-white shadow-sm' : 'bg-gray-50 opacity-60'}`}>
                        <div>
                            <h3 className="font-semibold text-gray-800">{u.full_name || u.email}</h3>
                            <p className="text-xs text-gray-500">{u.email} • <span className="capitalize font-medium">{u.role}</span></p>
                        </div>
                        <div className="flex gap-2">
                            <button onClick={() => toggleRole(u)} className="rounded-lg border px-3 py-1.5 text-xs font-medium text-gray-600 hover:bg-gray-50" title="Toggle role">
                                {u.role === 'admin' ? '👑 Admin' : '👤 Operator'}
                            </button>
                            <button onClick={() => toggleActive(u)} className={`rounded-lg border p-2 ${u.is_active ? 'text-green-600 hover:bg-red-50 hover:text-red-500' : 'text-red-500 hover:bg-green-50 hover:text-green-600'}`} title={u.is_active ? 'Deactivate' : 'Activate'}>
                                {u.is_active ? <UserCheck size={16} /> : <UserX size={16} />}
                            </button>
                            <button onClick={() => handleDelete(u.id)} className="rounded-lg border p-2 text-gray-500 hover:bg-red-50 hover:text-red-500" title="Delete">
                                <Trash2 size={16} />
                            </button>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}
