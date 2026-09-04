import { Bell, WifiOff } from 'lucide-react';
import { useAuthStore } from '../../stores/authStore';

interface TopbarProps {
  title: string;
  wsConnected?: boolean;
}

export default function Topbar({ title, wsConnected = true }: TopbarProps) {
  const { user } = useAuthStore();

  return (
    <header className="topbar">
      <div className="topbar-title">{title}</div>
      <div className="topbar-actions">
        <div className="ws-indicator">
          {wsConnected
            ? <><div className="ws-dot" /> Live</>
            : <><div className="ws-dot offline" /><WifiOff size={12} /> Offline</>
          }
        </div>
        <button className="btn btn-icon btn-ghost" aria-label="Notifications">
          <Bell size={16} />
        </button>
        <div className="topbar-user">
          <div style={{
            width: 24, height: 24, borderRadius: '50%',
            background: 'linear-gradient(135deg,#3b82f6,#8b5cf6)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: '0.65rem', fontWeight: 700, color: '#fff',
          }}>
            {user?.name?.[0] ?? 'A'}
          </div>
          <span>{user?.name ?? 'Admin'}</span>
        </div>
      </div>
    </header>
  );
}
