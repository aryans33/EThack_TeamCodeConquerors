import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import {
    LayoutDashboard, TrendingUp, FileText,
    MessageSquare, Star, LogOut, Activity,
    ChevronRight
} from 'lucide-react';
import './Sidebar.css';

const NAV_ITEMS = [
    { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { to: '/stocks', label: 'Markets', icon: TrendingUp },
    { to: '/watchlist', label: 'Watchlist', icon: Star },
    { to: '/documents', label: 'Documents', icon: FileText },
    { to: '/ask', label: 'AI Assistant', icon: MessageSquare },
];

export default function Sidebar() {
    const { user, logout } = useAuth();
    const navigate = useNavigate();

    const handleLogout = async () => {
        await logout();
        navigate('/login');
    };

    return (
        <aside className="sidebar">
            {/* Logo */}
            <div className="sidebar-logo">
                <div className="logo-icon"><Activity size={18} /></div>
                <span className="logo-text">FinAnalysis</span>
                <span className="logo-badge">AI</span>
            </div>

            {/* Nav */}
            <nav className="sidebar-nav">
                <div className="nav-section-label">Main Menu</div>
                {NAV_ITEMS.map(({ to, label, icon: Icon }) => (
                    <NavLink key={to} to={to} className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
                        <Icon size={18} />
                        <span>{label}</span>
                        <ChevronRight size={14} className="nav-arrow" />
                    </NavLink>
                ))}
            </nav>

            {/* User Footer */}
            <div className="sidebar-footer">
                <div className="user-info">
                    <div className="user-avatar">{user?.name?.[0]?.toUpperCase() || 'U'}</div>
                    <div className="user-details">
                        <div className="user-name">{user?.name || 'User'}</div>
                        <div className="user-plan">Free Plan</div>
                    </div>
                </div>
                <button className="logout-btn" onClick={handleLogout} title="Logout">
                    <LogOut size={16} />
                </button>
            </div>
        </aside>
    );
}
