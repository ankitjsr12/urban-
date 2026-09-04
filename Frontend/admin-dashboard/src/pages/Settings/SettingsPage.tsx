import { Settings, Users, Shield, Info } from 'lucide-react';

const ROLES = [
  { role: 'ADMIN', color: 'var(--clr-danger)', desc: 'Full system access — all pages, all actions', access: ['Dashboard','Fleet','Map','Incidents','Road Defects','Traffic','Vehicles','Analytics','Reports','Settings','User Management'] },
  { role: 'AUTHORITY', color: 'var(--clr-warning)', desc: 'Operational access — view and manage incidents/defects', access: ['Dashboard','Fleet','Map','Incidents','Road Defects','Traffic','Vehicles','Analytics','Reports'] },
  { role: 'DRIVER', color: 'var(--clr-accent)', desc: 'Mobile app access — monitoring and reporting only', access: ['Mobile: Monitoring','Mobile: Detections','Mobile: Incidents','Mobile: GPS'] },
  { role: 'CITIZEN', color: 'var(--clr-success)', desc: 'Citizen report submission only', access: ['Mobile: Submit Reports'] },
];

export default function SettingsPage() {
  return (
    <div className="fade-in">
      <div className="page-header">
        <h1>Settings & Administration</h1>
        <p>System configuration, user roles, and environment information</p>
      </div>

      {/* Role-based access */}
      <div className="card" style={{ marginBottom: 20 }}>
        <div className="card-header">
          <div>
            <div className="card-title"><Shield size={14} style={{ display: 'inline', marginRight: 6 }} />Role-Based Access Control</div>
            <div className="card-subtitle">Backend authorization is authoritative — frontend reflects allowed UI scope</div>
          </div>
        </div>
        <div className="grid-2">
          {ROLES.map(r => (
            <div key={r.role} className="card card-sm" style={{ borderLeft: `3px solid ${r.color}` }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                <span style={{ fontWeight: 700, color: r.color }}>{r.role}</span>
                <Shield size={14} color={r.color} />
              </div>
              <p style={{ fontSize: '0.78rem', color: 'var(--clr-text-secondary)', marginBottom: 10 }}>{r.desc}</p>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                {r.access.map(a => (
                  <span key={a} className="badge badge-default" style={{ fontSize: '0.65rem' }}>{a}</span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Environment config */}
      <div className="card" style={{ marginBottom: 20 }}>
        <div className="card-header">
          <div className="card-title"><Settings size={14} style={{ display: 'inline', marginRight: 6 }} />Environment Configuration</div>
        </div>
        <div className="table-wrap" style={{ border: 'none' }}>
          <table>
            <thead><tr><th>Variable</th><th>Current Value</th><th>Description</th></tr></thead>
            <tbody>
              {[
                { key: 'VITE_API_BASE_URL',  value: import.meta.env.VITE_API_BASE_URL || '(not set)', desc: 'Backend REST API base URL' },
                { key: 'VITE_WS_URL',        value: import.meta.env.VITE_WS_URL || '(not set)', desc: 'WebSocket base URL' },
                { key: 'VITE_MAP_PROVIDER',  value: import.meta.env.VITE_MAP_PROVIDER || 'leaflet', desc: 'Map tile provider' },
                { key: 'VITE_MOCK_MODE',     value: import.meta.env.VITE_MOCK_MODE || 'false', desc: 'Use mock data (dev only)' },
              ].map(({ key, value, desc }) => (
                <tr key={key}>
                  <td className="td-mono" style={{ color: 'var(--clr-accent)' }}>{key}</td>
                  <td className="td-mono">{value}</td>
                  <td className="td-muted">{desc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* User management placeholder */}
      <div className="card">
        <div className="card-header">
          <div className="card-title"><Users size={14} style={{ display: 'inline', marginRight: 6 }} />User Management</div>
        </div>
        <div className="alert alert-info">
          <Info size={16} />
          <span>
            User management connects to <code>POST /api/v1/auth/register</code> and admin-level user listing endpoints.
            Implement <code>GET /api/v1/admin/users</code> in the backend to enable full user management here.
          </span>
        </div>
        <div style={{ marginTop: 16 }}>
          <div className="table-wrap" style={{ border: 'none' }}>
            <table>
              <thead><tr><th>Name</th><th>Email</th><th>Role</th><th>Status</th></tr></thead>
              <tbody>
                {[
                  { name: 'Admin User',    email: 'admin@urbansense.in',    role: 'ADMIN',     active: true },
                  { name: 'City Authority', email: 'authority@kolkata.gov.in', role: 'AUTHORITY', active: true },
                  { name: 'Driver Rajan',  email: 'rajan@ksrtc.in',         role: 'DRIVER',    active: true },
                ].map(u => (
                  <tr key={u.email}>
                    <td style={{ fontWeight: 600 }}>{u.name}</td>
                    <td className="td-muted">{u.email}</td>
                    <td><span className="badge" style={{ background: ({ ADMIN:'rgba(239,68,68,0.15)',AUTHORITY:'rgba(245,158,11,0.15)',DRIVER:'rgba(59,130,246,0.15)',CITIZEN:'rgba(34,197,94,0.15)' })[u.role], color: ({ ADMIN:'var(--clr-danger)',AUTHORITY:'var(--clr-warning)',DRIVER:'var(--clr-accent)',CITIZEN:'var(--clr-success)' })[u.role] }}>{u.role}</span></td>
                    <td><span className={`badge badge-dot ${u.active ? 'badge-success' : 'badge-default'}`}>{u.active ? 'Active' : 'Inactive'}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
