import { useQuery } from '@tanstack/react-query';
import { getVehicles } from '../../services/detections';
import { confidencePct } from '../../utils';
import { AlertCircle } from 'lucide-react';

const VEHICLE_ICONS: Record<string, string> = {
  CAR: '🚗', BUS: '🚌', TRUCK: '🚚', MOTORCYCLE: '🏍️', AUTO: '🛺', BICYCLE: '🚲', OTHER: '🚐',
};

export default function VehiclesPage() {
  const { data: page, isLoading } = useQuery({
    queryKey: ['vehicles'],
    queryFn: () => getVehicles(200, 0),
  });

  const vehicles = page?.items ?? [];
  const typeCounts = vehicles.reduce<Record<string, number>>((acc, v) => {
    acc[v.vehicle_type] = (acc[v.vehicle_type] || 0) + 1;
    return acc;
  }, {});

  return (
    <div className="fade-in">
      <div className="page-header">
        <h1>Vehicle Registry</h1>
        <p>Detected vehicles with OCR plate recognition — {page?.total ?? 0} records</p>
      </div>

      {/* Type summary */}
      <div className="kpi-grid" style={{ marginBottom: 24 }}>
        {Object.entries(typeCounts).map(([type, count]) => (
          <div key={type} className="kpi-card">
            <div style={{ fontSize: '1.5rem' }}>{VEHICLE_ICONS[type] ?? '🚐'}</div>
            <div className="kpi-value" style={{ fontSize: '1.6rem' }}>{count}</div>
            <div className="kpi-label">{type}</div>
          </div>
        ))}
      </div>

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Type</th>
              <th>Plate Number</th>
              <th>OCR Confidence</th>
              <th>OCR Status</th>
              <th>Tracking ID</th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              Array.from({ length: 8 }).map((_, i) => (
                <tr key={i}>{Array.from({ length: 5 }).map((_, j) => (
                  <td key={j}><div className="skeleton" style={{ height: 16, width: '70%' }} /></td>
                ))}</tr>
              ))
            ) : vehicles.map(v => (
              <tr key={v.id}>
                <td><span style={{ fontWeight: 600 }}>{VEHICLE_ICONS[v.vehicle_type]} {v.vehicle_type}</span></td>
                <td>
                  {v.plate_number ? (
                    <span className="td-mono" style={{ background: 'var(--clr-bg-elevated)', padding: '3px 8px', borderRadius: 4, fontSize: '0.8rem', border: '1px solid var(--clr-border)' }}>
                      {v.plate_number}
                    </span>
                  ) : <span className="td-muted">—</span>}
                </td>
                <td>
                  {v.ocr_confidence != null ? (
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                      {(v.ocr_confidence ?? 0) < 0.75 && <AlertCircle size={12} color="var(--clr-warning)" />}
                      <span className="td-mono">{confidencePct(v.ocr_confidence)}</span>
                    </div>
                  ) : <span className="td-muted">—</span>}
                </td>
                <td>
                  {v.ocr_status ? (
                    <span className={`badge badge-dot ${v.ocr_status === 'VERIFIED' ? 'badge-success' : 'badge-warning'}`}>
                      {v.ocr_status}
                    </span>
                  ) : <span className="td-muted">—</span>}
                </td>
                <td className="td-mono td-muted">{v.tracking_id ?? '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
