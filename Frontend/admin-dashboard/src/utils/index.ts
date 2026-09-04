import type { Priority, IncidentStatus, DefectStatus, Density, BusStatus, DetectionType } from '../models';

export function formatDate(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' });
}

export function formatTime(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', hour12: true });
}

export function formatDateTime(iso: string): string {
  return `${formatDate(iso)}, ${formatTime(iso)}`;
}

export function formatRelative(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  if (diff < 60_000) return `${Math.floor(diff / 1000)}s ago`;
  if (diff < 3_600_000) return `${Math.floor(diff / 60_000)}m ago`;
  if (diff < 86_400_000) return `${Math.floor(diff / 3_600_000)}h ago`;
  return `${Math.floor(diff / 86_400_000)}d ago`;
}

export function priorityColor(p: Priority): string {
  return { LOW: '#22c55e', MEDIUM: '#f59e0b', HIGH: '#f97316', CRITICAL: '#ef4444' }[p] || '#6b7280';
}

export function priorityBg(p: Priority): string {
  return { LOW: 'badge-success', MEDIUM: 'badge-warning', HIGH: 'badge-orange', CRITICAL: 'badge-danger' }[p] || 'badge-default';
}

export function incidentStatusColor(s: IncidentStatus): string {
  return {
    NEW: '#6366f1',
    UNDER_REVIEW: '#f59e0b',
    VERIFIED: '#3b82f6',
    ASSIGNED: '#8b5cf6',
    RESOLVED: '#22c55e',
    REJECTED: '#6b7280',
  }[s] || '#6b7280';
}

export function defectStatusColor(s: DefectStatus): string {
  return {
    DETECTED: '#ef4444',
    VERIFIED: '#3b82f6',
    ASSIGNED: '#8b5cf6',
    IN_PROGRESS: '#f59e0b',
    RESOLVED: '#22c55e',
    REJECTED: '#6b7280',
  }[s] || '#6b7280';
}

export function densityColor(d: Density): string {
  return { LOW: '#22c55e', MEDIUM: '#f59e0b', HIGH: '#f97316', CRITICAL: '#ef4444' }[d] || '#6b7280';
}

export function busStatusColor(s: BusStatus): string {
  return { ACTIVE: '#22c55e', INACTIVE: '#6b7280', MAINTENANCE: '#f59e0b', OFFLINE: '#ef4444' }[s] || '#6b7280';
}

export function detectionLabel(t: DetectionType): string {
  return {
    POTHOLE: '🕳️ Pothole',
    DAMAGED_ROAD: '🚧 Damaged Road',
    WATERLOGGING: '💧 Waterlogging',
    TRAFFIC_SIGN: '🚦 Traffic Sign',
    ZEBRA_CROSSING: '🦓 Zebra Crossing',
    ROAD_DIVIDER: '🛣️ Road Divider',
    VEHICLE: '🚗 Vehicle',
    PEDESTRIAN: '🚶 Pedestrian',
    CHILD_RISK: '⚠️ Child Risk',
    TRAFFIC_HAZARD: '⚠️ Traffic Hazard',
  }[t] || t;
}

export function incidentTypeLabel(t: string): string {
  return {
    POSSIBLE_HIT_AND_RUN: 'Possible Hit & Run',
    DANGEROUS_DRIVING: 'Dangerous Driving',
    COLLISION_LIKE_EVENT: 'Collision-like Event',
    PEDESTRIAN_RISK: 'Pedestrian Risk',
    ROAD_HAZARD: 'Road Hazard',
    OTHER: 'Other',
  }[t] || t;
}

export function confidencePct(c: number): string {
  return `${Math.round(c * 100)}%`;
}

export function clamp(val: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, val));
}
