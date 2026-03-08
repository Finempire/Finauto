import { NavLink } from 'react-router-dom';
import type { User } from '@/types';
import { LayoutDashboard, Upload, Settings, FileText, Users, LogOut } from 'lucide-react';

interface Props {
    user: User;
    onLogout: () => void;
}

const links = [
    { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
    { to: '/upload', icon: Upload, label: 'Upload Wizard' },
    { to: '/settings', icon: Settings, label: 'Tally Settings' },
    { to: '/templates', icon: FileText, label: 'Templates' },
];

export default function Sidebar({ user, onLogout }: Props) {
    return (
        <aside className="flex w-64 flex-col bg-navy text-white shadow-xl">
            {/* Logo */}
            <div className="flex items-center gap-3 px-6 py-5 border-b border-white/10">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-accent font-bold text-lg">F</div>
                <div>
                    <h1 className="text-lg font-bold tracking-tight">FinAuto</h1>
                    <p className="text-xs text-white/50">Tally Automation</p>
                </div>
            </div>

            {/* Nav Links */}
            <nav className="flex-1 px-3 py-4 space-y-1">
                {links.map(({ to, icon: Icon, label }) => (
                    <NavLink
                        key={to}
                        to={to}
                        end={to === '/'}
                        className={({ isActive }) =>
                            `flex items-center gap-3 rounded-lg px-4 py-2.5 text-sm font-medium transition-all duration-200 ${isActive
                                ? 'bg-accent text-white shadow-md'
                                : 'text-white/70 hover:bg-white/10 hover:text-white'
                            }`
                        }
                    >
                        <Icon size={18} />
                        {label}
                    </NavLink>
                ))}

                {user.role === 'admin' && (
                    <NavLink
                        to="/admin/users"
                        className={({ isActive }) =>
                            `flex items-center gap-3 rounded-lg px-4 py-2.5 text-sm font-medium transition-all duration-200 ${isActive
                                ? 'bg-accent text-white shadow-md'
                                : 'text-white/70 hover:bg-white/10 hover:text-white'
                            }`
                        }
                    >
                        <Users size={18} />
                        User Management
                    </NavLink>
                )}
            </nav>

            {/* User + Logout */}
            <div className="border-t border-white/10 px-4 py-4">
                <div className="flex items-center gap-3">
                    <div className="flex h-9 w-9 items-center justify-center rounded-full bg-accent/30 text-sm font-bold uppercase">
                        {user.full_name?.[0] || user.email[0]}
                    </div>
                    <div className="flex-1 min-w-0">
                        <p className="truncate text-sm font-medium">{user.full_name || user.email}</p>
                        <p className="text-xs text-white/50 capitalize">{user.role}</p>
                    </div>
                    <button
                        onClick={onLogout}
                        className="rounded-lg p-2 text-white/50 hover:bg-white/10 hover:text-white transition-colors"
                        title="Logout"
                    >
                        <LogOut size={16} />
                    </button>
                </div>
            </div>
        </aside>
    );
}
