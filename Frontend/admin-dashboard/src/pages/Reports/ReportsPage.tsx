import { useState } from 'react';
import { FileText, Download, Filter } from 'lucide-react';

const REPORT_TYPES = [
  { id: 'daily',   label: '📅 Daily Report',   desc: 'Last 24 hours summary' },
  { id: 'weekly',  label: '📊 Weekly Report',  desc: 'Last 7 days trends' },
  { id: 'monthly', label: '📈 Monthly Report', desc: '30-day analysis' },
  { id: 'custom',  label: '🗂️ Custom Report',  desc: 'Define your own date range' },
];

export default function ReportsPage() {
  const [selected, setSelected] = useState('daily');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo]     = useState('');
  const [filterRoute, setFilterRoute] = useState('ALL');
  const [filterBus, setFilterBus] = useState('');
  const [filterEvent, setFilterEvent] = useState('ALL');

  function handleExport(format: 'PDF' | 'CSV') {
    // When backend provides export endpoints, call:
    // GET /api/v1/reports/export?format=pdf&from=...&to=...&type=...
    alert(`Export as ${format} — connect to /api/v1/reports/export when backend implements it.`);
  }

  return (
    <div className="fade-in">
      <div className="page-header">
        <h1>Reports</h1>
        <p>Generate and export reports for road defects, traffic, incidents, and fleet activity</p>
      </div>

      <div className="grid-2" style={{ marginBottom: 20 }}>
        {/* Report type selector */}
        <div className="card">
          <div className="card-header"><div className="card-title">Report Type</div></div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {REPORT_TYPES.map(r => (
              <button
                key={r.id}
                onClick={() => setSelected(r.id)}
                style={{
                  display: 'flex', alignItems: 'center', gap: 12,
                  padding: '12px 14px', borderRadius: 8,
                  border: selected === r.id ? '1px solid rgba(59,130,246,0.4)' : '1px solid var(--clr-border)',
                  background: selected === r.id ? 'var(--clr-accent-glow)' : 'transparent',
                  cursor: 'pointer', textAlign: 'left', width: '100%',
                  transition: 'all 0.15s',
                }}
              >
                <div>
                  <div style={{ fontSize: '0.875rem', fontWeight: 600, color: selected === r.id ? 'var(--clr-accent)' : 'var(--clr-text-primary)' }}>{r.label}</div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--clr-text-muted)' }}>{r.desc}</div>
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Filters */}
        <div className="card">
          <div className="card-header">
            <div className="card-title"><Filter size={14} style={{ display: 'inline', marginRight: 6 }} />Filters</div>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            {selected === 'custom' && (
              <div className="grid-2">
                <div className="form-group">
                  <label className="form-label">From Date</label>
                  <input type="date" className="form-input" value={dateFrom} onChange={e => setDateFrom(e.target.value)} />
                </div>
                <div className="form-group">
                  <label className="form-label">To Date</label>
                  <input type="date" className="form-input" value={dateTo} onChange={e => setDateTo(e.target.value)} />
                </div>
              </div>
            )}
            <div className="form-group">
              <label className="form-label">Route</label>
              <select className="form-input" value={filterRoute} onChange={e => setFilterRoute(e.target.value)}>
                <option value="ALL">All Routes</option>
                <option>Barasat → Esplanade</option>
                <option>Howrah → Salt Lake</option>
                <option>Garia → Park Street</option>
                <option>Dunlop → Kalighat</option>
              </select>
            </div>
            <div className="form-group">
              <label className="form-label">Bus Number</label>
              <input type="text" className="form-input" placeholder="e.g. BUS-102" value={filterBus} onChange={e => setFilterBus(e.target.value)} />
            </div>
            <div className="form-group">
              <label className="form-label">Event Type</label>
              <select className="form-input" value={filterEvent} onChange={e => setFilterEvent(e.target.value)}>
                <option value="ALL">All Events</option>
                <option>Pothole</option>
                <option>Waterlogging</option>
                <option>Traffic Hazard</option>
                <option>Incident</option>
                <option>Vehicle</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      {/* Preview panel */}
      <div className="card" style={{ marginBottom: 20 }}>
        <div className="card-header">
          <div className="card-title">Report Preview</div>
          <div style={{ display: 'flex', gap: 8 }}>
            <button className="btn btn-ghost btn-sm" onClick={() => handleExport('CSV')}>
              <Download size={14} /> Export CSV
            </button>
            <button className="btn btn-primary btn-sm" onClick={() => handleExport('PDF')}>
              <Download size={14} /> Export PDF
            </button>
          </div>
        </div>

        <div style={{ padding: '24px 0' }}>
          <div className="alert alert-info" style={{ marginBottom: 20 }}>
            <FileText size={16} />
            <span>
              Report generation connects to <code>/api/v1/reports/export</code> when available.
              Currently showing a data summary. Select report type and filters, then export.
            </span>
          </div>

          <div className="kpi-grid">
            {[
              { label: 'Total Detections',    value: '342' },
              { label: 'Potholes Reported',   value: '89' },
              { label: 'Incidents Logged',    value: '17' },
              { label: 'Buses Monitored',     value: '128' },
              { label: 'Routes Covered',      value: '4' },
              { label: 'Km Covered',          value: '2,840' },
            ].map(({ label, value }) => (
              <div key={label} className="kpi-card">
                <div className="kpi-value" style={{ fontSize: '1.6rem' }}>{value}</div>
                <div className="kpi-label">{label}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Past reports list */}
      <div className="card">
        <div className="card-header"><div className="card-title">Generated Reports</div></div>
        <div className="table-wrap" style={{ border: 'none' }}>
          <table>
            <thead><tr><th>Name</th><th>Type</th><th>Date Range</th><th>Generated</th><th>Actions</th></tr></thead>
            <tbody>
              {[
                { name: 'Daily Summary - Sep 01', type: 'Daily',   range: 'Sep 01 2026',        generated: '2 hours ago' },
                { name: 'Weekly Report - Aug W4',  type: 'Weekly',  range: 'Aug 24–31 2026',     generated: '1 day ago' },
                { name: 'Monthly Report - Aug',    type: 'Monthly', range: 'Aug 01–31 2026',     generated: '2 days ago' },
              ].map(r => (
                <tr key={r.name}>
                  <td style={{ fontWeight: 600 }}>{r.name}</td>
                  <td><span className="badge badge-accent">{r.type}</span></td>
                  <td className="td-muted">{r.range}</td>
                  <td className="td-muted">{r.generated}</td>
                  <td>
                    <button className="btn btn-ghost btn-sm" onClick={() => handleExport('PDF')}>
                      <Download size={12} /> Download
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
