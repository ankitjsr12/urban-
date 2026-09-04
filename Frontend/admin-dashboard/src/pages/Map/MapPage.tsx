import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { MapContainer, TileLayer, CircleMarker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import { getBuses } from '../../services/buses';
import { getIncidents } from '../../services/incidents';
import { getRoadDefects, getDetections } from '../../services/detections';
import { detectionLabel, formatRelative, confidencePct } from '../../utils';
import { Layers, ToggleLeft, ToggleRight } from 'lucide-react';

type LayerKey = 'buses' | 'potholes' | 'waterlogging' | 'incidents' | 'detections';

const LAYER_CONFIG: { key: LayerKey; label: string; color: string; emoji: string }[] = [
  { key: 'buses',      label: 'Buses',       color: '#3b82f6', emoji: '🚌' },
  { key: 'potholes',   label: 'Potholes',    color: '#ef4444', emoji: '🕳️' },
  { key: 'waterlogging', label: 'Waterlogging', color: '#f59e0b', emoji: '💧' },
  { key: 'incidents',  label: 'Incidents',   color: '#8b5cf6', emoji: '🚨' },
  { key: 'detections', label: 'Detections',  color: '#22c55e', emoji: '📍' },
];

export default function MapPage() {
  const [layers, setLayers] = useState<Record<LayerKey, boolean>>({
    buses: true, potholes: true, waterlogging: true, incidents: true, detections: false,
  });

  function toggle(k: LayerKey) {
    setLayers(prev => ({ ...prev, [k]: !prev[k] }));
  }

  const { data: busPage } = useQuery({ queryKey: ['buses'], queryFn: () => getBuses(100) });
  const { data: incPage } = useQuery({ queryKey: ['incidents'], queryFn: () => getIncidents(200) });
  const { data: defPage } = useQuery({ queryKey: ['road-defects'], queryFn: () => getRoadDefects(200) });
  const { data: detPage } = useQuery({ queryKey: ['detections'], queryFn: () => getDetections(100) });

  const buses = busPage?.items ?? [];
  const incidents = incPage?.items ?? [];
  const defects = defPage?.items ?? [];
  const detections = detPage?.items ?? [];

  const potholes = defects.filter(d => d.defect_type === 'POTHOLE');
  const waterlogging = defects.filter(d => d.defect_type === 'WATERLOGGING');

  return (
    <div className="fade-in" style={{ height: 'calc(100vh - 108px)', display: 'flex', flexDirection: 'column', gap: 0 }}>
      <div className="page-header">
        <h1>GIS Intelligence Map</h1>
        <p>Spatial view of all urban sensing data across the city</p>
      </div>

      <div style={{ flex: 1, display: 'grid', gridTemplateColumns: '200px 1fr', gap: 16, minHeight: 0 }}>
        {/* Layer panel */}
        <div className="card" style={{ padding: '14px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 14 }}>
            <Layers size={16} color="var(--clr-accent)" />
            <span className="card-title">Map Layers</span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            {LAYER_CONFIG.map(({ key, label, color, emoji }) => (
              <button
                key={key}
                onClick={() => toggle(key)}
                style={{
                  display: 'flex', alignItems: 'center', gap: 8,
                  padding: '8px 10px', borderRadius: 6, border: 'none',
                  background: layers[key] ? `${color}18` : 'transparent',
                  cursor: 'pointer', width: '100%', textAlign: 'left',
                  transition: 'all 0.15s',
                }}
              >
                <div style={{ width: 10, height: 10, borderRadius: '50%', background: layers[key] ? color : 'var(--clr-text-muted)', flexShrink: 0 }} />
                <span style={{ flex: 1, fontSize: '0.8rem', color: layers[key] ? 'var(--clr-text-primary)' : 'var(--clr-text-muted)', fontWeight: 500 }}>
                  {emoji} {label}
                </span>
                {layers[key] ? <ToggleRight size={14} color={color} /> : <ToggleLeft size={14} color="var(--clr-text-muted)" />}
              </button>
            ))}
          </div>
          <div style={{ marginTop: 20 }}>
            <div className="map-legend">
              <div style={{ fontSize: '0.7rem', fontWeight: 600, color: 'var(--clr-text-muted)', marginBottom: 6 }}>LEGEND</div>
              {LAYER_CONFIG.map(({ key, label, color }) => (
                <div key={key} className="map-legend-item">
                  <div className="map-dot" style={{ background: color }} />
                  {label}
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Map */}
        <div className="map-container">
          <MapContainer center={[22.5726, 88.3639]} zoom={12} style={{ height: '100%', width: '100%' }}>
            <TileLayer
              url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
              attribution='&copy; CARTO'
            />

            {/* Buses */}
            {layers.buses && buses.map(bus =>
              bus.latitude && bus.longitude ? (
                <CircleMarker key={bus.id} center={[bus.latitude, bus.longitude]} radius={10} color="#3b82f6" fillColor="#3b82f6" fillOpacity={0.8}>
                  <Popup><strong>🚌 {bus.bus_number}</strong><br />{bus.route_name}<br />Status: {bus.status}<br />Speed: {bus.speed ?? '—'} km/h</Popup>
                </CircleMarker>
              ) : null
            )}

            {/* Potholes */}
            {layers.potholes && potholes.map(d => (
              <CircleMarker key={d.id} center={[d.latitude, d.longitude]} radius={7} color="#ef4444" fillColor="#ef4444" fillOpacity={0.7}>
                <Popup>🕳️ <strong>Pothole</strong><br />Severity: {d.severity}<br />Conf: {confidencePct(d.confidence)}<br />{formatRelative(d.detected_at)}</Popup>
              </CircleMarker>
            ))}

            {/* Waterlogging */}
            {layers.waterlogging && waterlogging.map(d => (
              <CircleMarker key={d.id} center={[d.latitude, d.longitude]} radius={8} color="#f59e0b" fillColor="#f59e0b" fillOpacity={0.7}>
                <Popup>💧 <strong>Waterlogging</strong><br />Severity: {d.severity}<br />Conf: {confidencePct(d.confidence)}</Popup>
              </CircleMarker>
            ))}

            {/* Incidents */}
            {layers.incidents && incidents.map(inc => (
              <CircleMarker key={inc.id} center={[inc.latitude, inc.longitude]} radius={9} color="#8b5cf6" fillColor="#8b5cf6" fillOpacity={0.8}>
                <Popup>🚨 <strong>{inc.incident_type.replace(/_/g, ' ')}</strong><br />Priority: {inc.priority}<br />Status: {inc.status}</Popup>
              </CircleMarker>
            ))}

            {/* Detections */}
            {layers.detections && detections.filter(d => d.latitude && d.longitude).map(d => (
              <CircleMarker key={d.id} center={[d.latitude!, d.longitude!]} radius={5} color="#22c55e" fillColor="#22c55e" fillOpacity={0.6}>
                <Popup>{detectionLabel(d.detection_type)}<br />Conf: {confidencePct(d.confidence)}</Popup>
              </CircleMarker>
            ))}
          </MapContainer>
        </div>
      </div>
    </div>
  );
}
