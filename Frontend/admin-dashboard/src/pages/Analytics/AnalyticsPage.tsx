import { useQuery } from '@tanstack/react-query';
import { getDetections, getRoadDefects } from '../../services/detections';
import { getIncidents } from '../../services/incidents';
import { getTrafficEvents } from '../../services/traffic';
import { getBuses } from '../../services/buses';
import { detectionLabel } from '../../utils';
import type { DetectionType } from '../../models';
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, PieChart, Pie, Cell, Legend,
} from 'recharts';

const COLORS = ['#3b82f6','#f59e0b','#f97316','#ef4444','#22c55e','#8b5cf6','#14b8a6','#ec4899'];

export default function AnalyticsPage() {
  const { data: detPage }  = useQuery({ queryKey: ['detections'],   queryFn: () => getDetections(200) });
  const { data: defPage }  = useQuery({ queryKey: ['road-defects'], queryFn: () => getRoadDefects(200) });
  const { data: incPage }  = useQuery({ queryKey: ['incidents'],    queryFn: () => getIncidents(200) });
  const { data: trafPage } = useQuery({ queryKey: ['traffic'],      queryFn: () => getTrafficEvents(48) });
  const { data: busPage }  = useQuery({ queryKey: ['buses'],        queryFn: () => getBuses(100) });

  const detections = detPage?.items ?? [];
  const defects    = defPage?.items ?? [];
  const incidents  = incPage?.items ?? [];
  const traffic    = trafPage?.items ?? [];
  const buses      = busPage?.items ?? [];

  // Detection type breakdown
  const detTypeCounts = detections.reduce<Record<string, number>>((acc, d) => {
    acc[d.detection_type] = (acc[d.detection_type] || 0) + 1;
    return acc;
  }, {});
  const detPieData = Object.entries(detTypeCounts).map(([name, value]) => ({
    name: detectionLabel(name as DetectionType),
    value,
  }));

  // Defect severity breakdown
  const defSeverity = defects.reduce<Record<string, number>>((acc, d) => {
    acc[d.severity] = (acc[d.severity] || 0) + 1;
    return acc;
  }, {});
  const defSeverityData = Object.entries(defSeverity).map(([name, value]) => ({ name, value }));

  // Incident trend (group by day roughly using index)

  // Bus status breakdown
  const busStatus = buses.reduce<Record<string, number>>((acc, b) => {
    acc[b.status] = (acc[b.status] || 0) + 1;
    return acc;
  }, {});
  const busStatusData = Object.entries(busStatus).map(([name, value]) => ({ name, value }));

  // Avg traffic speed over time
  const speedData = traffic.slice(0, 24).reverse().map((t, i) => ({
    h: `${i}h`,
    speed: Math.round(t.average_speed ?? 0),
    vehicles: t.total_vehicles,
  }));

  return (
    <div className="fade-in">
      <div className="page-header">
        <h1>Analytics & Trends</h1>
        <p>Aggregated intelligence from the Kolkata transit sensing network</p>
      </div>

      {/* Summary KPIs */}
      <div className="kpi-grid" style={{ marginBottom: 24 }}>
        <div className="kpi-card"><div className="kpi-value" style={{ color: 'var(--clr-accent)' }}>{detections.length}</div><div className="kpi-label">Total Detections</div></div>
        <div className="kpi-card"><div className="kpi-value" style={{ color: 'var(--clr-warning)' }}>{defects.length}</div><div className="kpi-label">Road Defects</div></div>
        <div className="kpi-card"><div className="kpi-value" style={{ color: 'var(--clr-danger)' }}>{incidents.length}</div><div className="kpi-label">Incidents</div></div>
        <div className="kpi-card"><div className="kpi-value" style={{ color: 'var(--clr-success)' }}>{buses.filter(b => b.status === 'ACTIVE').length}</div><div className="kpi-label">Active Buses</div></div>
      </div>

      <div className="grid-2" style={{ marginBottom: 20 }}>
        {/* Detection type breakdown */}
        <div className="card">
          <div className="card-header"><div className="card-title">Detection Types</div></div>
          <div className="chart-container" style={{ height: 260 }}>
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={detPieData} cx="50%" cy="50%" outerRadius={90} dataKey="value" paddingAngle={3}>
                  {detPieData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                </Pie>
                <Tooltip contentStyle={{ background:'var(--clr-bg-elevated)',border:'1px solid var(--clr-border)',borderRadius:6,fontSize:11 }} />
                <Legend iconSize={10} wrapperStyle={{ fontSize: 11 }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Defect severity */}
        <div className="card">
          <div className="card-header"><div className="card-title">Defect Severity Distribution</div></div>
          <div className="chart-container" style={{ height: 260 }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={defSeverityData}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--clr-border)" />
                <XAxis dataKey="name" tick={{ fill:'var(--clr-text-muted)',fontSize:11 }} />
                <YAxis tick={{ fill:'var(--clr-text-muted)',fontSize:11 }} />
                <Tooltip contentStyle={{ background:'var(--clr-bg-elevated)',border:'1px solid var(--clr-border)',borderRadius:6,fontSize:12 }} />
                <Bar dataKey="value" radius={[4,4,0,0]}>
                  {defSeverityData.map((entry, i) => {
                    const c = { LOW:'#22c55e',MEDIUM:'#f59e0b',HIGH:'#f97316',CRITICAL:'#ef4444' }[entry.name] || COLORS[i];
                    return <Cell key={i} fill={c} />;
                  })}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <div className="grid-2" style={{ marginBottom: 20 }}>
        {/* Fleet status */}
        <div className="card">
          <div className="card-header"><div className="card-title">Fleet Status Breakdown</div></div>
          <div className="chart-container" style={{ height: 220 }}>
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={busStatusData} cx="50%" cy="50%" innerRadius={50} outerRadius={80} paddingAngle={4} dataKey="value">
                  {busStatusData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                </Pie>
                <Tooltip contentStyle={{ background:'var(--clr-bg-elevated)',border:'1px solid var(--clr-border)',borderRadius:6,fontSize:12 }} />
                <Legend iconSize={10} wrapperStyle={{ fontSize: 11 }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Speed & Volume */}
        <div className="card">
          <div className="card-header"><div className="card-title">Speed vs. Volume Correlation</div></div>
          <div className="chart-container" style={{ height: 220 }}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={speedData}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--clr-border)" />
                <XAxis dataKey="h" tick={{ fill:'var(--clr-text-muted)',fontSize:11 }} />
                <YAxis yAxisId="l" tick={{ fill:'var(--clr-text-muted)',fontSize:11 }} />
                <YAxis yAxisId="r" orientation="right" tick={{ fill:'var(--clr-text-muted)',fontSize:11 }} />
                <Tooltip contentStyle={{ background:'var(--clr-bg-elevated)',border:'1px solid var(--clr-border)',borderRadius:6,fontSize:12 }} />
                <Legend wrapperStyle={{ fontSize: 11 }} />
                <Line yAxisId="l" type="monotone" dataKey="speed" stroke="#22c55e" strokeWidth={2} dot={false} name="Speed (km/h)" />
                <Line yAxisId="r" type="monotone" dataKey="vehicles" stroke="#3b82f6" strokeWidth={2} dot={false} name="Vehicles" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Route Analytics Table */}
      <div className="card">
        <div className="card-header"><div className="card-title">Route Performance (Mock Data)</div><div className="card-subtitle">Backend route analytics endpoint not yet implemented</div></div>
        <div className="table-wrap" style={{ border: 'none' }}>
          <table>
            <thead>
              <tr>
                <th>Route</th><th>Avg Speed</th><th>Expected</th><th>Actual</th><th>Delay</th><th>Traffic Level</th><th>Detections</th>
              </tr>
            </thead>
            <tbody>
              {[
                { route: 'Barasat → Esplanade', speed: 28, expected: 55, actual: 72, delay: 17, density: 'HIGH', detections: 42 },
                { route: 'Howrah → Salt Lake',  speed: 34, expected: 40, actual: 48, delay:  8, density: 'MEDIUM', detections: 28 },
                { route: 'Garia → Park Street', speed: 22, expected: 50, actual: 71, delay: 21, density: 'CRITICAL', detections: 61 },
                { route: 'Dunlop → Kalighat',   speed: 38, expected: 45, actual: 50, delay:  5, density: 'LOW', detections: 19 },
              ].map(r => (
                <tr key={r.route}>
                  <td style={{ fontWeight: 600 }}>{r.route}</td>
                  <td>{r.speed} km/h</td>
                  <td>{r.expected} min</td>
                  <td>{r.actual} min</td>
                  <td style={{ color: r.delay > 15 ? 'var(--clr-danger)' : r.delay > 5 ? 'var(--clr-warning)' : 'var(--clr-success)', fontWeight: 600 }}>+{r.delay} min</td>
                  <td><span className="badge badge-dot" style={{ background: ({ LOW:'rgba(34,197,94,0.15)',MEDIUM:'rgba(245,158,11,0.15)',HIGH:'rgba(249,115,22,0.15)',CRITICAL:'rgba(239,68,68,0.15)' })[r.density], color: ({ LOW:'var(--clr-success)',MEDIUM:'var(--clr-warning)',HIGH:'var(--clr-orange)',CRITICAL:'var(--clr-danger)' })[r.density] }}>{r.density}</span></td>
                  <td>{r.detections}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
