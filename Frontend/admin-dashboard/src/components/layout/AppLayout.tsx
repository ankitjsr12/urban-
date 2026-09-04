import { Outlet, useLocation } from 'react-router-dom';
import Sidebar from './Sidebar';
import Topbar from './Topbar';
import { Toaster } from 'react-hot-toast';

const TITLES: Record<string, string> = {
  '/dashboard':    'Dashboard',
  '/fleet':        'Live Fleet Monitor',
  '/map':          'GIS Intelligence Map',
  '/incidents':    'Incident Management',
  '/road-defects': 'Road Defect Monitor',
  '/traffic':      'Traffic Analytics',
  '/vehicles':     'Vehicle Registry',
  '/analytics':    'Analytics & Trends',
  '/reports':      'Reports',
  '/settings':     'Settings & Users',
};

export default function AppLayout() {
  const { pathname } = useLocation();
  const title = TITLES[pathname] ?? 'AI UrbanSense';

  return (
    <div className="app-layout">
      <Sidebar />
      <div className="main-content">
        <Topbar title={title} />
        <main className="page-content">
          <Outlet />
        </main>
      </div>
      <Toaster
        position="top-right"
        toastOptions={{
          style: {
            background: 'var(--clr-bg-elevated)',
            color: 'var(--clr-text-primary)',
            border: '1px solid var(--clr-border)',
            fontSize: '0.825rem',
          },
        }}
      />
    </div>
  );
}
