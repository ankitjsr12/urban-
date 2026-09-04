import { useQuery } from '@tanstack/react-query';
import { getTrafficEvents } from '../../services/traffic';
import type { Density } from '../../models';

import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, BarChart, Bar, Cell, PieChart, Pie,
} from 'recharts';

const DENSITY_COLORS = { LOW: '#22c55e', MEDIUM: '#f59e0b', HIGH: '#f97316', CRITICAL: '#ef4444' };

export default function TrafficPage() {
  const { data: page } = useQuery({
    queryKey: ['traffic'],
    queryFn: () => getTrafficEvents(48, 0),
    refetchInterval: 60_000,
  });

  const events = page?.items ?? [];

  const totalVehicles = events.reduce((s, e) => s + e.total_vehicles, 0);
  const totalCars     = events.reduce((s, e) => s + e.cars, 0);
  const totalBikes    = events.reduce((s, e) => s + e.bikes, 0);
  const totalTrucks   = events.reduce((s, e) => s + e.trucks, 0);
  const totalBuses    = events.reduce((s, e) => s + e.buses, 0);
  const totalAutos    = events.reduce((s, e) => s + e.autos, 0);
  const avgSpeed      = events.length ? Math.round(events.reduce((s, e) => s + (e.average_speed ?? 0), 0) / events.length) : 0;

  const trendData = events.slice(0, 24).reverse().map((e, i) => ({
    h: `${i}h`,
    vehicles: e.total_vehicles,
    speed: Math.round(e.average_speed ?? 0),
  }));

  const categoryData = [
    { name: 'Cars',        value: totalCars,   fill: '#3b82f6' },
    { name: 'Bikes',       value: totalBikes,  fill: '#8b5cf6' },
    { name: 'Buses',       value: totalBuses,  fill: '#22c55e' },
    { name: 'Trucks',      value: totalTrucks, fill: '#f97316' },
    { name: 'Autos',       value: totalAutos,  fill: '#f59e0b' },
  ];

  const densityCounts = events.reduce<Record<string, number>>((acc, e) => {
    acc[e.traffic_density] = (acc[e.traffic_density] || 0) + 1;
    return acc;
  }, {});
  const densityData = Object.entries(densityCounts).map(([name, value]) => ({ name, value }));

  const STAT_CARDS = [
    { label: 'Total Vehicles (24h)', value: totalVehicles.toLocaleString() },
    { label: 'Cars', value: totalCars.toLocaleString() },
    { label: 'Motorcycles/Bikes', value: totalBikes.toLocaleString() },
    { label: 'Buses', value: totalBuses.toLocaleString() },
    { label: 'Trucks', value: totalTrucks.toLocaleString() },
    { label: 'Autos', value: totalAutos.toLocaleString() },
    { label: 'Avg Speed (km/h)', value: avgSpeed.toString() },
  ];

  return (
    <div className="fade-in">
      <div className="page-header">
        <h1>Traffic Analytics</h1>
        <p>Vehicle counts, speed, and congestion trends from fleet sensors</p>
      </div>

      {/* KPI */}
      <div className="kpi-grid" style={{ marginBottom: 24 }}>
        {STAT_CARDS.map(({ label, value }) => (
          <div key={label} className="kpi-card">
            <div className="kpi-value" style={{ color: 'var(--clr-accent)', fontSize: '1.6rem' }}>{value}</div>
            <div className="kpi-label">{label}</div>
          </div>
        ))}
      </div>

      <div className="grid-2" style={{ marginBottom: 20 }}>
        {/* Volume Trend */}
        <div className="card">
          <div className="card-header">
            <div><div className="card-title">Vehicle Volume (24h)</div><div className="card-subtitle">Hourly detections</div></div>
          </div>
          <div className="chart-container">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={trendData}>
                <defs>
                  <linearGradient id="vGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--clr-border)" />
                <XAxis dataKey="h" tick={{ fill:'var(--clr-text-muted)',fontSize:11 }} />
                <YAxis tick={{ fill:'var(--clr-text-muted)',fontSize:11 }} />
                <Tooltip contentStyle={{ background:'var(--clr-bg-elevated)',border:'1px solid var(--clr-border)',borderRadius:6,fontSize:12 }} />
                <Area type="monotone" dataKey="vehicles" stroke="#3b82f6" fill="url(#vGrad)" strokeWidth={2} name="Vehicles" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Speed Trend */}
        <div className="card">
          <div className="card-header">
            <div><div className="card-title">Average Speed (km/h)</div><div className="card-subtitle">Fleet-wide speed trend</div></div>
          </div>
          <div className="chart-container">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={trendData}>
                <defs>
                  <linearGradient id="sGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#22c55e" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#22c55e" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--clr-border)" />
                <XAxis dataKey="h" tick={{ fill:'var(--clr-text-muted)',fontSize:11 }} />
                <YAxis tick={{ fill:'var(--clr-text-muted)',fontSize:11 }} />
                <Tooltip contentStyle={{ background:'var(--clr-bg-elevated)',border:'1px solid var(--clr-border)',borderRadius:6,fontSize:12 }} />
                <Area type="monotone" dataKey="speed" stroke="#22c55e" fill="url(#sGrad)" strokeWidth={2} name="Avg Speed" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <div className="grid-2">
        {/* Category Breakdown */}
        <div className="card">
          <div className="card-header"><div className="card-title">Vehicle Category Distribution</div></div>
          <div className="chart-container">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={categoryData} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="var(--clr-border)" horizontal={false} />
                <XAxis type="number" tick={{ fill:'var(--clr-text-muted)',fontSize:11 }} />
                <YAxis type="category" dataKey="name" tick={{ fill:'var(--clr-text-muted)',fontSize:11 }} width={60} />
                <Tooltip contentStyle={{ background:'var(--clr-bg-elevated)',border:'1px solid var(--clr-border)',borderRadius:6,fontSize:12 }} />
                <Bar dataKey="value" radius={[0,4,4,0]}>
                  {categoryData.map((entry, i) => <Cell key={i} fill={entry.fill} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Density Distribution */}
        <div className="card">
          <div className="card-header"><div className="card-title">Traffic Density Distribution</div></div>
          <div className="chart-container">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={densityData} cx="50%" cy="50%" innerRadius={55} outerRadius={90} paddingAngle={4} dataKey="value" label={(props) => `${props.name ?? ''} ${(((props.percent as number) ?? 0) * 100).toFixed(0)}%`} labelLine={false}>
                  {densityData.map((entry, i) => (
                    <Cell key={i} fill={DENSITY_COLORS[entry.name as Density] ?? '#6b7280'} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ background:'var(--clr-bg-elevated)',border:'1px solid var(--clr-border)',borderRadius:6,fontSize:12 }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
}
