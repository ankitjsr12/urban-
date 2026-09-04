import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { getBuses } from '../../services/buses';
import { wsManager } from '../../services/websocket';
import type { Bus } from '../../models';
import { busStatusColor, formatRelative } from '../../utils';
import { RefreshCw } from 'lucide-react';

// Fix leaflet default icon
delete (L.Icon.Default.prototype as unknown as Record<string, unknown>)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

function createBusIcon(color: string) {
  return L.divIcon({
    className: '',
    html: `<div style="width:32px;height:32px;border-radius:50%;background:${color};border:3px solid #fff;display:flex;align-items:center;justify-content:center;box-shadow:0 2px 8px rgba(0,0,0,0.4);font-size:14px;">🚌</div>`,
    iconSize: [32, 32],
    iconAnchor: [16, 16],
  });
}

function FitBounds({ buses }: { buses: Bus[] }) {
  const map = useMap();
  useEffect(() => {
    const pts = buses.filter(b => b.latitude && b.longitude).map(b => [b.latitude!, b.longitude!] as [number, number]);
    if (pts.length > 0) map.fitBounds(pts, { padding: [40, 40] });
  }, [buses, map]);
  return null;
}

export default function FleetPage() {
  const { data: page, isLoading, refetch } = useQuery({
    queryKey: ['buses'],
    queryFn: () => getBuses(100, 0),
    refetchInterval: 30_000,
  });

  const [liveBuses, setLiveBuses] = useState<Record<string, Partial<Bus>>>({});
  const [selected, setSelected] = useState<Bus | null>(null);

  useEffect(() => {
    const unsub = wsManager.subscribe('buses', (ev) => {
      const { bus_id, latitude, longitude, speed } = ev as unknown as { bus_id: string; latitude: number; longitude: number; speed: number };
      if (bus_id) setLiveBuses(prev => ({ ...prev, [bus_id]: { latitude, longitude, speed } }));
    });
    return unsub;
  }, []);

  const buses: Bus[] = (page?.items ?? []).map(b => ({
    ...b,
    ...(liveBuses[b.id] || {}),
  }));

  const activeBuses = buses.filter(b => b.status === 'ACTIVE');
  const statusCounts = buses.reduce<Record<string, number>>((acc, b) => {
    acc[b.status] = (acc[b.status] || 0) + 1;
    return acc;
  }, {});

  return (
    <div className="fade-in" style={{ height: 'calc(100vh - 108px)', display: 'flex', flexDirection: 'column', gap: 16 }}>
      <div className="page-header" style={{ marginBottom: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div>
            <h1>Live Fleet Monitor</h1>
            <p>Real-time bus locations and status across the Kolkata network</p>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <div style={{ display: 'flex', gap: 8 }}>
              {Object.entries(statusCounts).map(([status, count]) => (
                <div key={status} className="badge badge-dot" style={{ background: `${busStatusColor(status as 'ACTIVE')}20`, color: busStatusColor(status as 'ACTIVE') }}>
                  {count} {status}
                </div>
              ))}
            </div>
            <button className="btn btn-ghost btn-sm" onClick={() => refetch()}>
              <RefreshCw size={14} /> Refresh
            </button>
          </div>
        </div>
      </div>

      <div style={{ flex: 1, display: 'grid', gridTemplateColumns: '320px 1fr', gap: 16, minHeight: 0 }}>
        {/* Bus List */}
        <div className="card" style={{ overflow: 'hidden', display: 'flex', flexDirection: 'column', padding: 0 }}>
          <div style={{ padding: '14px 16px', borderBottom: '1px solid var(--clr-border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span className="card-title">Fleet ({buses.length})</span>
            <span style={{ fontSize: '0.7rem', color: 'var(--clr-success)' }}>{activeBuses.length} active</span>
          </div>
          <div style={{ flex: 1, overflowY: 'auto', padding: 8 }}>
            {isLoading ? (
              Array.from({ length: 5 }).map((_, i) => (
                <div key={i} className="skeleton" style={{ height: 64, marginBottom: 8, borderRadius: 8 }} />
              ))
            ) : (
              buses.map((bus) => (
                <div
                  key={bus.id}
                  onClick={() => setSelected(bus)}
                  style={{
                    padding: '10px 12px',
                    borderRadius: 8,
                    cursor: 'pointer',
                    marginBottom: 4,
                    background: selected?.id === bus.id ? 'var(--clr-accent-glow)' : 'transparent',
                    border: selected?.id === bus.id ? '1px solid rgba(59,130,246,0.3)' : '1px solid transparent',
                    transition: 'all 0.15s',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 4 }}>
                    <span style={{ fontWeight: 700, fontSize: '0.875rem' }}>{bus.bus_number}</span>
                    <span className="badge badge-dot" style={{ background: `${busStatusColor(bus.status)}20`, color: busStatusColor(bus.status) }}>
                      {bus.status}
                    </span>
                  </div>
                  <div style={{ fontSize: '0.72rem', color: 'var(--clr-text-secondary)' }}>
                    {bus.route_name || bus.registration_number}
                  </div>
                  {bus.speed != null && (
                    <div style={{ fontSize: '0.7rem', color: 'var(--clr-text-muted)', marginTop: 2 }}>
                      {bus.speed} km/h
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </div>

        {/* Map */}
        <div className="map-container">
          <MapContainer
            center={[22.5726, 88.3639]}
            zoom={11}
            style={{ height: '100%', width: '100%' }}
          >
            <TileLayer
              url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
              attribution='&copy; <a href="https://carto.com/">CARTO</a>'
            />
            <FitBounds buses={buses.filter(b => b.latitude && b.longitude)} />
            {buses.map((bus) =>
              bus.latitude && bus.longitude ? (
                <Marker
                  key={bus.id}
                  position={[bus.latitude, bus.longitude]}
                  icon={createBusIcon(busStatusColor(bus.status))}
                  eventHandlers={{ click: () => setSelected(bus) }}
                >
                  <Popup>
                    <div style={{ minWidth: 200, fontFamily: 'var(--font-sans)' }}>
                      <strong>{bus.bus_number}</strong><br />
                      <span style={{ fontSize: 12, color: '#888' }}>{bus.route_name}</span>
                      <hr style={{ margin: '8px 0', borderColor: '#333' }} />
                      <div style={{ fontSize: 12, lineHeight: 1.8 }}>
                        <b>Status:</b> {bus.status}<br />
                        <b>Speed:</b> {bus.speed ?? '—'} km/h<br />
                        <b>Reg:</b> {bus.registration_number}<br />
                        {bus.last_update && <><b>Updated:</b> {formatRelative(bus.last_update)}</>}
                      </div>
                    </div>
                  </Popup>
                </Marker>
              ) : null
            )}
          </MapContainer>
        </div>
      </div>

      {/* Selected bus detail panel */}
      {selected && (
        <div className="card card-sm fade-in" style={{ position: 'fixed', bottom: 24, right: 24, width: 300, zIndex: 500 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 12 }}>
            <div>
              <div style={{ fontWeight: 700, fontSize: '1rem' }}>{selected.bus_number}</div>
              <div style={{ fontSize: '0.75rem', color: 'var(--clr-text-secondary)' }}>{selected.route_name}</div>
            </div>
            <button className="btn btn-ghost btn-icon btn-sm" onClick={() => setSelected(null)}>✕</button>
          </div>
          <div className="info-grid">
            <div className="info-item"><label>Status</label><span className="badge badge-dot" style={{ background: `${busStatusColor(selected.status)}20`, color: busStatusColor(selected.status) }}>{selected.status}</span></div>
            <div className="info-item"><label>Speed</label><span>{selected.speed ?? '—'} km/h</span></div>
            <div className="info-item"><label>Latitude</label><span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem' }}>{selected.latitude?.toFixed(4) ?? '—'}</span></div>
            <div className="info-item"><label>Longitude</label><span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem' }}>{selected.longitude?.toFixed(4) ?? '—'}</span></div>
          </div>
        </div>
      )}
    </div>
  );
}
