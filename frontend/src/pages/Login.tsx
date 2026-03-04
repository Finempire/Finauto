import { useState } from 'react';
import { toast } from 'sonner';
import { login, getMe } from '@/api/client';
import type { User } from '@/types';

interface Props {
    onLogin: (user: User) => void;
}

export default function Login({ onLogin }: Props) {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        try {
            const { access_token } = await login(email, password);
            localStorage.setItem('token', access_token);
            const user = await getMe();
            onLogin(user);
            toast.success('Welcome back!');
        } catch (err: any) {
            toast.error(err.response?.data?.detail || 'Login failed');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-navy via-navy-dark to-navy p-4">
            <div className="w-full max-w-md">
                {/* Logo */}
                <div className="mb-8 text-center">
                    <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-accent text-2xl font-bold text-white shadow-lg shadow-accent/30">
                        F
                    </div>
                    <h1 className="text-3xl font-bold text-white">FinAuto</h1>
                    <p className="mt-1 text-white/60">Tally Automation Platform</p>
                </div>

                {/* Form */}
                <form
                    onSubmit={handleSubmit}
                    className="rounded-2xl bg-white p-8 shadow-2xl"
                >
                    <h2 className="mb-6 text-xl font-semibold text-gray-800">Sign in to your account</h2>

                    <div className="space-y-4">
                        <div>
                            <label className="mb-1.5 block text-sm font-medium text-gray-700">Email</label>
                            <input
                                id="login-email"
                                type="email"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                required
                                className="w-full rounded-lg border border-gray-300 px-4 py-2.5 text-sm focus:border-accent focus:outline-none focus:ring-2 focus:ring-accent/20 transition-all"
                                placeholder="you@company.com"
                            />
                        </div>

                        <div>
                            <label className="mb-1.5 block text-sm font-medium text-gray-700">Password</label>
                            <input
                                id="login-password"
                                type="password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                required
                                className="w-full rounded-lg border border-gray-300 px-4 py-2.5 text-sm focus:border-accent focus:outline-none focus:ring-2 focus:ring-accent/20 transition-all"
                                placeholder="••••••••"
                            />
                        </div>
                    </div>

                    <button
                        id="login-submit"
                        type="submit"
                        disabled={loading}
                        className="mt-6 w-full rounded-lg bg-accent py-2.5 text-sm font-semibold text-white shadow-md shadow-accent/30 transition-all hover:bg-accent-dark disabled:opacity-60"
                    >
                        {loading ? (
                            <span className="flex items-center justify-center gap-2">
                                <span className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                                Signing in...
                            </span>
                        ) : (
                            'Sign In'
                        )}
                    </button>
                </form>
            </div>
        </div>
    );
}
