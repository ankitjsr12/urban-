import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getRoadDefects } from '../../services/detections';
import { formatDateTime, confidencePct, defectStatusColor } from '../../utils';
import type { DefectStatus } from '../../models';
import { Radio, RotateCcw, MapPin } from 'lucide-react';

const DEFECT_TYPE_ICONS: Record<string, string> = {
  POTHOLE: '🕳️', WATERLOGGING: '💧', DAMAGED_ROAD: '🚧',
  MISSING_SIGN: '🚫', ZEBRA_CROSSING_ISSUE: '🦓', ROAD_DIVIDER_ISSUE: '🛣️',
};
const SEVERITY_COLORS: Record<string, string> = {
  LOW: 'var(--clr-success)', MEDIUM: 'var(--clr-warning)',
  HIGH: 'var(--clr-orange)', CRITICAL: 'var(--clr-danger)',
};

export default function RoadDefectsPage() {
  const [filterType, setFilterType] = useState('ALL');
  const [filterStatus, setFilterStatus] = useState('ALL');

  const { data: page, isLoading, error, refetch } = useQuery({
    queryKey: ['road-defects'],
    queryFn: () => getRoadDefects(200, 0),
    refetchInterval: 30_000,
  });

  const items = (page?.items ?? []).filter(d =>
    (filterType === 'ALL' || d.defect_type === filterType) &&
    (filterStatus === 'ALL' || d.status === filterStatus)
  );

  const types = [...new Set((page?.items ?? []).map(d => d.defect_type))];
  const statuses: DefectStatus[] = ['DETECTED','VERIFIED','ASSIGNED','IN_PROGRESS','RESOLVED','REJECTED'];

  if (error) return (
    <div className="state-box">
      <Radio size={40} color="var(--clr-danger)" />
      <p>Unable to load road defects.</p>
      <button className="btn btn-ghost" onClick={() => refetch()}><RotateCcw size={14} /> Retry</button>
    </div>
  );

  return (
    <div className="fade-in">
      <div className="page-header">
        <h1>Road Defect Monitor</h1>
        <p>Detected road surface issues reported by the fleet — {page?.total ?? 0} total</p>
      </div>

      {/* Summary cards */}
      <div className="kpi-grid" style={{ marginBottom: 24 }}>
        {['POTHOLE','WATERLOGGING','DAMAGED_ROAD'].map(t => {
          const count = (page?.items ?? []).filter(d => d.defect_type === t).length;
          return (
            <div key={t} className="kpi-card">
              <div style={{ fontSize: '1.5rem' }}>{DEFECT_TYPE_ICONS[t] ?? '📍'}</div>
              <div className="kpi-value" style={{ fontSize: '1.6rem' }}>{count}</div>
              <div className="kpi-label">{t.replace(/_/g, ' ')}</div>
            </div>
          );
        })}
        {['DETECTED','RESOLVED'].map(s => {
          const count = (page?.items ?? []).filter(d => d.status === s).length;
          return (
            <div key={s} className="kpi-card">
              <div className="kpi-value" style={{ color: defectStatusColor(s as DefectStatus) }}>{count}</div>
              <div className="kpi-label">{s}</div>
            </div>
          );
        })}
      </div>

      {/* Filters */}
      <div style={{ display: 'flex', gap: 16, marginBottom: 16, flexWrap: 'wrap' }}>
        <div className="filters-bar" style={{ marginBottom: 0 }}>
          <span style={{ fontSize: '0.75rem', color: 'var(--clr-text-muted)', fontWeight: 600 }}>TYPE:</span>
          <button className={`chip ${filterType === 'ALL' ? 'active' : ''}`} onClick={() => setFilterType('ALL')}>All</button>
          {types.map(t => <button key={t} className={`chip ${filterType === t ? 'active' : ''}`} onClick={() => setFilterType(t)}>{DEFECT_TYPE_ICONS[t] ?? ''} {t.replace(/_/g,' ')}</button>)}
        </div>
        <div className="filters-bar" style={{ marginBottom: 0 }}>
          <span style={{ fontSize: '0.75rem', color: 'var(--clr-text-muted)', fontWeight: 600 }}>STATUS:</span>
          <button className={`chip ${filterStatus === 'ALL' ? 'active' : ''}`} onClick={() => setFilterStatus('ALL')}>All</button>
          {statuses.map(s => <button key={s} className={`chip ${filterStatus === s ? 'active' : ''}`} onClick={() => setFilterStatus(s)}>{s.replace(/_/g,' ')}</button>)}
        </div>
      </div>

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Type</th>
              <th>Severity</th>
              <th>Confidence</th>
              <th>Location</th>
              <th>Bus</th>
              <th>Detected</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              Array.from({ length: 8 }).map((_, i) => (
                <tr key={i}>{Array.from({ length: 7 }).map((_, j) => (
                  <td key={j}><div className="skeleton" style={{ height: 16, width: '80%' }} /></td>
                ))}</tr>
              ))
            ) : items.length === 0 ? (
              <tr><td colSpan={7}><div className="state-box"><p>No defects match the selected filters.</p></div></td></tr>
            ) : (
              items.map(d => (
                <tr key={d.id}>
                  <td>
                    <span style={{ fontWeight: 600 }}>
                      {DEFECT_TYPE_ICONS[d.defect_type] ?? '📍'} {d.defect_type.replace(/_/g,' ')}
                    </span>
                  </td>
                  <td>
                    <span className="badge" style={{ background: `${SEVERITY_COLORS[d.severity]}20`, color: SEVERITY_COLORS[d.severity] }}>
                      {d.severity}
                    </span>
                  </td>
                  <td className="td-mono">{confidencePct(d.confidence)}</td>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                      <MapPin size={12} color="var(--clr-text-muted)" />
                      <span className="td-mono td-muted">{d.latitude.toFixed(4)}, {d.longitude.toFixed(4)}</span>
                    </div>
                  </td>
                  <td className="td-mono td-muted">{d.bus_id?.slice(0, 8) ?? '—'}</td>
                  <td className="td-muted">{formatDateTime(d.detected_at)}</td>
                  <td>
                    <span className="badge badge-dot" style={{ background: `${defectStatusColor(d.status)}20`, color: defectStatusColor(d.status) }}>
                      {d.status.replace(/_/g,' ')}
                    </span>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
