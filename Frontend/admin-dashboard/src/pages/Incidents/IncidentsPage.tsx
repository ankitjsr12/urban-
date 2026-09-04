import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getIncidents, patchIncidentStatus } from '../../services/incidents';
import { formatDateTime, confidencePct, incidentTypeLabel, priorityBg } from '../../utils';
import type { Incident, IncidentStatus, Priority } from '../../models';
import { AlertTriangle, Eye, CheckCircle, XCircle, RotateCcw, UserCheck } from 'lucide-react';
import toast from 'react-hot-toast';

const STATUS_FLOW: Record<string, string[]> = {
  NEW:          ['UNDER_REVIEW', 'REJECTED'],
  UNDER_REVIEW: ['VERIFIED',     'REJECTED'],
  VERIFIED:     ['ASSIGNED',     'RESOLVED'],
  ASSIGNED:     ['RESOLVED',     'REJECTED'],
  RESOLVED:     [],
  REJECTED:     [],
};

function StatusBadge({ status }: { status: IncidentStatus }) {
  const map: Record<IncidentStatus, string> = {
    NEW: 'badge-accent', UNDER_REVIEW: 'badge-warning', VERIFIED: 'badge-accent',
    ASSIGNED: 'badge-purple', RESOLVED: 'badge-success', REJECTED: 'badge-default',
  };
  return <span className={`badge badge-dot ${map[status]}`}>{status.replace('_', ' ')}</span>;
}

function IncidentModal({ incident, onClose }: { incident: Incident; onClose: () => void }) {
  const qc = useQueryClient();
  const mutation = useMutation({
    mutationFn: ({ id, status }: { id: string; status: string }) => patchIncidentStatus(id, status),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['incidents'] }); toast.success('Incident status updated'); onClose(); },
    onError: () => toast.error('Failed to update status'),
  });

  const nextStatuses = STATUS_FLOW[incident.status] ?? [];

  return (
    <div className="modal-overlay" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal modal-lg">
        <div className="modal-header">
          <h2>🚨 Incident Detail</h2>
          <button className="btn btn-ghost btn-icon btn-sm" onClick={onClose}>✕</button>
        </div>
        <div className="modal-body">
          <div style={{ display: 'flex', gap: 12, alignItems: 'center', marginBottom: 20 }}>
            <span className={`badge badge-dot ${priorityBg(incident.priority as Priority)}`} style={{ fontSize: '0.8rem', padding: '5px 12px' }}>
              {incident.priority} PRIORITY
            </span>
            <StatusBadge status={incident.status} />
          </div>

          <div className="info-grid" style={{ marginBottom: 20 }}>
            <div className="info-item"><label>Incident Type</label><span>{incidentTypeLabel(incident.incident_type)}</span></div>
            <div className="info-item"><label>AI Confidence</label><span>{confidencePct(incident.confidence ?? 0)}</span></div>
            <div className="info-item"><label>Timestamp</label><span>{formatDateTime(incident.timestamp)}</span></div>
            <div className="info-item"><label>Bus ID</label><span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem' }}>{incident.bus_id?.slice(0, 8) ?? '—'}</span></div>
            <div className="info-item"><label>Latitude</label><span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem' }}>{incident.latitude.toFixed(6)}</span></div>
            <div className="info-item"><label>Longitude</label><span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem' }}>{incident.longitude.toFixed(6)}</span></div>
          </div>

          {incident.description && (
            <div style={{ marginBottom: 16 }}>
              <div className="form-label" style={{ marginBottom: 6 }}>Description</div>
              <div style={{ background: 'var(--clr-bg-elevated)', padding: 12, borderRadius: 6, fontSize: '0.875rem', color: 'var(--clr-text-secondary)' }}>
                {incident.description}
              </div>
            </div>
          )}

          <div className="alert alert-info" style={{ marginBottom: 0 }}>
            <Eye size={16} />
            <span>Evidence viewer — connect to <code>POST /api/v1/evidence/upload</code> and <code>GET /api/v1/incidents/{'{id}'}/evidence</code></span>
          </div>
        </div>

        {nextStatuses.length > 0 && (
          <div className="modal-footer">
            <button className="btn btn-ghost" onClick={onClose}>Close</button>
            {nextStatuses.map(s => (
              <button
                key={s}
                className={`btn ${s === 'REJECTED' ? 'btn-danger' : s === 'RESOLVED' ? 'btn-success' : 'btn-primary'}`}
                disabled={mutation.isPending}
                onClick={() => mutation.mutate({ id: incident.id, status: s })}
              >
                {s === 'VERIFIED' && <CheckCircle size={14} />}
                {s === 'REJECTED' && <XCircle size={14} />}
                {s === 'ASSIGNED' && <UserCheck size={14} />}
                {s === 'RESOLVED' && <CheckCircle size={14} />}
                {s.replace('_', ' ')}
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

const PRIORITIES = ['ALL','CRITICAL','HIGH','MEDIUM','LOW'];
const STATUSES   = ['ALL','NEW','UNDER_REVIEW','VERIFIED','ASSIGNED','RESOLVED','REJECTED'];

export default function IncidentsPage() {
  const [filterPriority, setFilterPriority] = useState('ALL');
  const [filterStatus, setFilterStatus] = useState('ALL');
  const [selected, setSelected] = useState<Incident | null>(null);

  const { data: page, isLoading, error, refetch } = useQuery({
    queryKey: ['incidents'],
    queryFn: () => getIncidents(200, 0),
    refetchInterval: 30_000,
  });

  const items = (page?.items ?? []).filter(i =>
    (filterPriority === 'ALL' || i.priority === filterPriority) &&
    (filterStatus === 'ALL' || i.status === filterStatus)
  );

  if (error) return (
    <div className="state-box">
      <AlertTriangle size={40} color="var(--clr-danger)" />
      <p>Unable to load incidents.</p>
      <button className="btn btn-ghost" onClick={() => refetch()}><RotateCcw size={14} /> Retry</button>
    </div>
  );

  return (
    <div className="fade-in">
      <div className="page-header">
        <h1>Incident Management</h1>
        <p>Review, verify, and resolve reported incidents across the network</p>
      </div>

      {/* Filters */}
      <div style={{ display: 'flex', gap: 16, marginBottom: 16, flexWrap: 'wrap' }}>
        <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
          <span style={{ fontSize: '0.75rem', color: 'var(--clr-text-muted)', fontWeight: 600 }}>PRIORITY:</span>
          {PRIORITIES.map(p => (
            <button key={p} className={`chip ${filterPriority === p ? 'active' : ''}`} onClick={() => setFilterPriority(p)}>
              {p}
            </button>
          ))}
        </div>
        <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
          <span style={{ fontSize: '0.75rem', color: 'var(--clr-text-muted)', fontWeight: 600 }}>STATUS:</span>
          {STATUSES.map(s => (
            <button key={s} className={`chip ${filterStatus === s ? 'active' : ''}`} onClick={() => setFilterStatus(s)}>
              {s.replace('_',' ')}
            </button>
          ))}
        </div>
      </div>

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Priority</th>
              <th>Type</th>
              <th>Confidence</th>
              <th>Location</th>
              <th>Timestamp</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              Array.from({ length: 6 }).map((_, i) => (
                <tr key={i}>{Array.from({ length: 7 }).map((_, j) => (
                  <td key={j}><div className="skeleton" style={{ height: 16, width: '80%' }} /></td>
                ))}</tr>
              ))
            ) : items.length === 0 ? (
              <tr><td colSpan={7}>
                <div className="state-box"><AlertTriangle size={32} /><p>No incidents match the current filters.</p></div>
              </td></tr>
            ) : (
              items.map((inc) => (
                <tr key={inc.id}>
                  <td><span className={`badge badge-dot ${priorityBg(inc.priority as Priority)}`}>{inc.priority}</span></td>
                  <td style={{ fontWeight: 600 }}>{incidentTypeLabel(inc.incident_type)}</td>
                  <td className="td-mono">{confidencePct(inc.confidence ?? 0)}</td>
                  <td className="td-mono td-muted">{inc.latitude.toFixed(4)}, {inc.longitude.toFixed(4)}</td>
                  <td className="td-muted">{formatDateTime(inc.timestamp)}</td>
                  <td><StatusBadge status={inc.status} /></td>
                  <td>
                    <button className="btn btn-ghost btn-sm" onClick={() => setSelected(inc)}>
                      <Eye size={14} /> View
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {selected && <IncidentModal incident={selected} onClose={() => setSelected(null)} />}
    </div>
  );
}
