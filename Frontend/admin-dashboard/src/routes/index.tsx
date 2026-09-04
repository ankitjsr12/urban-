import { createBrowserRouter, Navigate } from 'react-router-dom';
import AppLayout from '../components/layout/AppLayout';
import RequireAuth from './RequireAuth';
import LoginPage from '../pages/Login/LoginPage';
import DashboardPage from '../pages/Dashboard/DashboardPage';
import FleetPage from '../pages/Fleet/FleetPage';
import MapPage from '../pages/Map/MapPage';
import IncidentsPage from '../pages/Incidents/IncidentsPage';
import RoadDefectsPage from '../pages/RoadDefects/RoadDefectsPage';
import TrafficPage from '../pages/Traffic/TrafficPage';
import VehiclesPage from '../pages/Vehicles/VehiclesPage';
import AnalyticsPage from '../pages/Analytics/AnalyticsPage';
import ReportsPage from '../pages/Reports/ReportsPage';
import SettingsPage from '../pages/Settings/SettingsPage';

export const router = createBrowserRouter([
  { path: '/login', element: <LoginPage /> },
  {
    element: <RequireAuth><AppLayout /></RequireAuth>,
    children: [
      { index: true, element: <Navigate to="/dashboard" replace /> },
      { path: '/dashboard',    element: <DashboardPage /> },
      { path: '/fleet',        element: <FleetPage /> },
      { path: '/map',          element: <MapPage /> },
      { path: '/incidents',    element: <IncidentsPage /> },
      { path: '/road-defects', element: <RoadDefectsPage /> },
      { path: '/traffic',      element: <TrafficPage /> },
      { path: '/vehicles',     element: <VehiclesPage /> },
      { path: '/analytics',    element: <AnalyticsPage /> },
      { path: '/reports',      element: <ReportsPage /> },
      { path: '/settings',     element: <SettingsPage /> },
    ],
  },
  { path: '*', element: <Navigate to="/dashboard" replace /> },
]);
