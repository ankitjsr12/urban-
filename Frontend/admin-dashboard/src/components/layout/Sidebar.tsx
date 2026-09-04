import { NavLink, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard, Bus, Map, AlertTriangle, BarChart2, Car,
  FileText, Settings, Activity, Shield, LogOut, Radio,
} from 'lucide-react';
import { useAuthStore } from '../../stores/authStore';

const NAV = [
  { section: 'Overview', items: [
    { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  ]},
  { section: 'Operations', items: [
    { to: '/fleet',       label: 'Live Fleet',    icon: Bus },
    { to: '/map',         label: 'GIS Map',       icon: Map },
    { to: '/incidents',   label: 'Incidents',     icon: AlertTriangle },
  ]},
  { section: 'Intelligence', items: [
    { to: '/road-defects', label: 'Road Defects', icon: Radio },
    { to: '/traffic',      label: 'Traffic',      icon: Activity },
    { to: '/vehicles',     label: 'Vehicles',     icon: Car },
  ]},
  { section: 'Analytics', items: [
    { to: '/analytics', label: 'Analytics',   icon: BarChart2 },
    { to: '/reports',   label: 'Reports',     icon: FileText },
  ]},
  { section: 'Admin', items: [
    { to: '/settings', label: 'Settings', icon: Settings },
  ]},
];

export default function Sidebar() {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();

  function handleLogout() {
    logout();
    navigate('/login');
  }

  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <div className="sidebar-logo-icon">
          <Shield size={18} color="#fff" />
        </div>
        <div className="sidebar-logo-text">
          <h2>AI UrbanSense</h2>
          <p>Urban Intelligence</p>
        </div>
      </div>

      <nav className="sidebar-nav">
        {NAV.map(({ section, items }) => (
          <div key={section}>
            <div className="sidebar-section-label">{section}</div>
            {items.map(({ to, label, icon: Icon }) => (
              <NavLink
                key={to}
                to={to}
                className={({ isActive }) => `sidebar-link${isActive ? ' active' : ''}`}
              >
                <Icon size={16} />
                {label}
              </NavLink>
            ))}
          </div>
        ))}
      </nav>

      <div className="sidebar-footer">
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
          <div style={{
            width: 32, height: 32, borderRadius: '50%',
            background: 'linear-gradient(135deg,#3b82f6,#8b5cf6)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: '0.75rem', fontWeight: 700, color: '#fff', flexShrink: 0,
          }}>
            {user?.name?.[0] ?? 'A'}
          </div>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--clr-text-primary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {user?.name ?? 'Admin'}
            </div>
            <div style={{ fontSize: '0.7rem', color: 'var(--clr-text-muted)' }}>{user?.role}</div>
          </div>
        </div>
        <button className="btn btn-ghost btn-sm" style={{ width: '100%', justifyContent: 'center' }} onClick={handleLogout}>
          <LogOut size={14} /> Logout
        </button>
      </div>
    </aside>
  );
}
