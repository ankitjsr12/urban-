import { useQuery } from '@tanstack/react-query';
import { getOverview } from '../../services/analytics';
import { getIncidents } from '../../services/incidents';
import { getTrafficEvents } from '../../services/traffic';
import { getRoadDefects } from '../../services/detections';
import {
  Bus, AlertTriangle, Activity, Shield, Zap,
  TrendingUp, TrendingDown, RotateCcw,
} from 'lucide-react';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, PieChart, Pie, Cell, BarChart, Bar, Legend,
} from 'recharts';
import { formatRelative, priorityBg, incidentTypeLabel, confidencePct } from '../../utils';
import type { Priority } from '../../models';

function KPICard({ label, value, icon: Icon, color, change }: {
  label: string; value: string | number; icon: React.ElementType;
  color: string; change?: { pct: number; up: boolean };
}) {
  return (
    <div className="kpi-card">
      <div className="kpi-icon" style={{ background: `${color}20` }}>
        <Icon size={20} color={color} />
      </div>
      <div>
        <div className="kpi-value" style={{ color }}>{typeof value === 'number' ? value.toLocaleString() : value}</div>
        <div className="kpi-label">{label}</div>
      </div>
      {change && (
        <div className={`kpi-change ${change.up ? 'up' : 'down'}`}>
          {change.up ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
          {change.pct}% vs yesterday
        </div>
      )}
    </div>
  );
}

const CHART_COLORS = ['#3b82f6', '#f59e0b', '#f97316', '#ef4444'];

export default function DashboardPage() {
  const { data: overview, isLoading: ovLoading, error: ovError, refetch: ovRefetch } = useQuery({
    queryKey: ['overview'],
    queryFn: getOverview,
    refetchInterval: 30_000,
  });

  const { data: incidentsPage } = useQuery({
    queryKey: ['incidents'],
    queryFn: () => getIncidents(10, 0),
    refetchInterval: 30_000,
  });

  const { data: trafficPage } = useQuery({
    queryKey: ['traffic'],
    queryFn: () => getTrafficEvents(24, 0),
    refetchInterval: 30_000,
  });

  const { data: defectsPage } = useQuery({
    queryKey: ['road-defects'],
    queryFn: () => getRoadDefects(50, 0),
    refetchInterval: 30_000,
  });

  const incidents = incidentsPage?.items ?? [];
  const trafficEvents = trafficPage?.items ?? [];
  const defects = defectsPage?.items ?? [];

  // Traffic trend chart data
  const trafficChartData = trafficEvents.slice(0, 12).reverse().map((t, i) => ({
    time: `${i * 2}h`,
    vehicles: t.total_vehicles,
    speed: Math.round(t.average_speed ?? 0),
  }));

  // Defect type distribution
  const defectTypes = defects.reduce<Record<string, number>>((acc, d) => {
    acc[d.defect_type] = (acc[d.defect_type] || 0) + 1;
    return acc;
  }, {});
  const defectPieData = Object.entries(defectTypes).map(([name, value]) => ({ name, value }));

  // Priority distribution
  const priorityCounts = incidents.reduce<Record<string, number>>((acc, i) => {
    acc[i.priority] = (acc[i.priority] || 0) + 1;
    return acc;
  }, {});
  const priorityBarData = ['LOW','MEDIUM','HIGH','CRITICAL'].map((p) => ({
    priority: p, count: priorityCounts[p] || 0,
  }));

  if (ovError) {
    return (
      <div className="state-box">
        <AlertTriangle size={40} color="var(--clr-danger)" />
        <p>Unable to load dashboard data.</p>
        <button className="btn btn-ghost" onClick={() => ovRefetch()}>
          <RotateCcw size={14} /> Retry
        </button>
      </div>
    );
  }

  return (
    <div className="fade-in">
      <div className="page-header">
        <h1>Command Center</h1>
        <p>Real-time urban intelligence overview for Kolkata transit network</p>
      </div>

      {/* KPI Cards */}
      {ovLoading ? (
        <div className="kpi-grid">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="kpi-card">
              <div className="skeleton" style={{ height: 40, width: 40 }} />
              <div className="skeleton" style={{ height: 32, width: '60%' }} />
              <div className="skeleton" style={{ height: 14, width: '80%' }} />
            </div>
          ))}
        </div>
      ) : (
        <div className="kpi-grid">
          <KPICard label="Active Buses" value={overview?.active_buses ?? 0} icon={Bus} color="var(--clr-accent)" change={{ pct: 3, up: true }} />
          <KPICard label="Total Buses" value={overview?.total_buses ?? 0} icon={Bus} color="var(--clr-teal)" />
          <KPICard label="Road Defects" value={overview?.total_road_defects ?? 0} icon={Zap} color="var(--clr-warning)" change={{ pct: 12, up: true }} />
          <KPICard label="Traffic Events" value={overview?.total_traffic_events ?? 0} icon={Activity} color="var(--clr-purple)" />
          <KPICard label="Active Incidents" value={overview?.total_incidents ?? 0} icon={AlertTriangle} color="var(--clr-danger)" change={{ pct: 5, up: false }} />
          <KPICard label="High Priority" value={overview?.high_priority_incidents ?? 0} icon={Shield} color="var(--clr-orange)" />
          <KPICard label="Total Detections" value={overview?.total_detections ?? 0} icon={Activity} color="var(--clr-success)" change={{ pct: 18, up: true }} />
        </div>
      )}

      {/* Charts Row */}
      <div className="grid-2" style={{ marginBottom: 20 }}>
        {/* Traffic Trend */}
        <div className="card">
          <div className="card-header">
            <div>
              <div className="card-title">Traffic Volume Trend</div>
              <div className="card-subtitle">Vehicles detected over last 24h</div>
            </div>
          </div>
          <div className="chart-container">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={trafficChartData}>
                <defs>
                  <linearGradient id="trafficGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--clr-border)" />
                <XAxis dataKey="time" tick={{ fill: 'var(--clr-text-muted)', fontSize: 11 }} />
                <YAxis tick={{ fill: 'var(--clr-text-muted)', fontSize: 11 }} />
                <Tooltip contentStyle={{ background: 'var(--clr-bg-elevated)', border: '1px solid var(--clr-border)', borderRadius: 6, fontSize: 12 }} />
                <Area type="monotone" dataKey="vehicles" stroke="#3b82f6" fill="url(#trafficGrad)" strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Incident Priority */}
        <div className="card">
          <div className="card-header">
            <div>
              <div className="card-title">Incident Priority Distribution</div>
              <div className="card-subtitle">Current period breakdown</div>
            </div>
          </div>
          <div className="chart-container">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={priorityBarData}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--clr-border)" />
                <XAxis dataKey="priority" tick={{ fill: 'var(--clr-text-muted)', fontSize: 11 }} />
                <YAxis tick={{ fill: 'var(--clr-text-muted)', fontSize: 11 }} />
                <Tooltip contentStyle={{ background: 'var(--clr-bg-elevated)', border: '1px solid var(--clr-border)', borderRadius: 6, fontSize: 12 }} />
                <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                  {priorityBarData.map((_, i) => (
                    <Cell key={i} fill={CHART_COLORS[i]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Bottom Row */}
      <div className="grid-2">
        {/* Recent Incidents */}
        <div className="card">
          <div className="card-header">
            <div className="card-title">Recent Incidents</div>
            <a href="/incidents" className="btn btn-ghost btn-sm">View all</a>
          </div>
          {incidents.length === 0 ? (
            <div className="state-box" style={{ padding: '24px' }}>
              <p>No incidents recorded</p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {incidents.slice(0, 6).map((inc) => (
                <div key={inc.id} className={`card card-sm priority-stripe-${inc.priority}`} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 10 }}>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: '0.825rem', fontWeight: 600, color: 'var(--clr-text-primary)' }}>
                      {incidentTypeLabel(inc.incident_type)}
                    </div>
                    <div style={{ fontSize: '0.72rem', color: 'var(--clr-text-muted)', marginTop: 2 }}>
                      {formatRelative(inc.created_at)} · Conf: {confidencePct(inc.confidence ?? 0)}
                    </div>
                  </div>
                  <span className={`badge badge-dot ${priorityBg(inc.priority as Priority)}`}>{inc.priority}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Defect Breakdown */}
        <div className="card">
          <div className="card-header">
            <div className="card-title">Road Defect Types</div>
          </div>
          {defectPieData.length === 0 ? (
            <div className="state-box" style={{ padding: '24px' }}><p>No data</p></div>
          ) : (
            <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
              <div style={{ height: 200, flex: 1 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie data={defectPieData} cx="50%" cy="50%" innerRadius={50} outerRadius={80} paddingAngle={4} dataKey="value">
                      {defectPieData.map((_, i) => (
                        <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip contentStyle={{ background: 'var(--clr-bg-elevated)', border: '1px solid var(--clr-border)', borderRadius: 6, fontSize: 12 }} />
                    <Legend iconType="circle" iconSize={10} wrapperStyle={{ fontSize: 11 }} />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
