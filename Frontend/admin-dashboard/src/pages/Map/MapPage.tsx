import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { MapContainer, TileLayer, CircleMarker, Circle, Popup, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import { getBuses } from '../../services/buses';
import { getIncidents, getNearbyIncidents } from '../../services/incidents';
import { getRoadDefects, getDetections } from '../../services/detections';
import { detectionLabel, formatRelative, confidencePct } from '../../utils';
import { Layers, ToggleLeft, ToggleRight, MapPin, Radio } from 'lucide-react';

type LayerKey = 'buses' | 'potholes' | 'waterlogging' | 'traffic' | 'incidents' | 'heatmap' | 'detections';

const LAYER_CONFIG: { key: LayerKey; label: string; color: string; emoji: string }[] = [
  { key: 'buses',        label: 'Buses & Fleet', color: '#3b82f6', emoji: '🚌' },
  { key: 'potholes',     label: 'Potholes',      color: '#ef4444', emoji: '🕳️' },
  { key: 'waterlogging', label: 'Waterlogging',  color: '#f97316', emoji: '💧' },
  { key: 'traffic',      label: 'Traffic Events',color: '#eab308', emoji: '🟡' },
  { key: 'incidents',    label: 'Incidents',     color: '#dc2626', emoji: '🚨' },
  { key: 'heatmap',      label: 'Heatmap Zones', color: '#8b5cf6', emoji: '🔥' },
  { key: 'detections',   label: 'Detections',    color: '#22c55e', emoji: '📍' },
];

function MapCenterController({ center }: { center: [number, number] | null }) {
  const map = useMap();
  useEffect(() => {
    if (center) {
      map.setView(center, 14, { animate: true });
    }
  }, [center, map]);
  return null;
}

export default function MapPage() {
  const [layers, setLayers] = useState<Record<LayerKey, boolean>>({
    buses: true,
    potholes: true,
    waterlogging: true,
    traffic: true,
    incidents: true,
    heatmap: true,
    detections: false,
  });

  const [userLocation, setUserLocation] = useState<[number, number] | null>(null);
  const [locating, setLocating] = useState(false);

  function toggle(k: LayerKey) {
    setLayers(prev => ({ ...prev, [k]: !prev[k] }));
  }

  function handleLocateMe() {
    if (!navigator.geolocation) {
      alert('Geolocation is not supported by your browser');
      return;
    }
    setLocating(true);
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setUserLocation([pos.coords.latitude, pos.coords.longitude]);
        setLocating(false);
      },
      () => {
        setLocating(false);
        // Fallback default
        setUserLocation([22.5726, 88.3639]);
      },
      { enableHighAccuracy: true, timeout: 10000 }
    );
  }

  const { data: busPage } = useQuery({ queryKey: ['buses'], queryFn: () => getBuses(100) });
  const { data: incPage } = useQuery({ queryKey: ['incidents'], queryFn: () => getIncidents(200) });
  const { data: defPage } = useQuery({ queryKey: ['road-defects'], queryFn: () => getRoadDefects(200) });
  const { data: detPage } = useQuery({ queryKey: ['detections'], queryFn: () => getDetections(100) });

  // If user location is acquired, query PostGIS nearby incidents endpoint
  const { data: nearbyData } = useQuery({
    queryKey: ['nearby-incidents', userLocation?.[0], userLocation?.[1]],
    queryFn: () => (userLocation ? getNearbyIncidents(userLocation[0], userLocation[1], 10) : null),
    enabled: !!userLocation,
  });

  const buses = busPage?.items ?? [];
  const incidents = nearbyData?.items ?? incPage?.items ?? [];
  const defects = defPage?.items ?? [];
  const detections = detPage?.items ?? [];

  const potholes = defects.filter(d => d.defect_type === 'POTHOLE' || d.defect_type === 'CRACK' || d.defect_type === 'ROAD_DAMAGE');
  const waterlogging = defects.filter(d => d.defect_type === 'WATERLOGGING');
  const trafficIncidents = incidents.filter(i => i.incident_type === 'TRAFFIC' || i.incident_type === 'CONGESTION');
  const otherIncidents = incidents.filter(i => i.incident_type !== 'TRAFFIC' && i.incident_type !== 'CONGESTION');

  return (
    <div className="fade-in" style={{ height: 'calc(100vh - 108px)', display: 'flex', flexDirection: 'column', gap: 0 }}>
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1>GIS Intelligence & Hazard Map</h1>
          <p>Real-time PostGIS spatial sensing layer across city grid</p>
        </div>
        <button
          onClick={handleLocateMe}
          className="btn btn-primary"
          style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.85rem' }}
          disabled={locating}
        >
          <MapPin size={15} />
          {locating ? 'Acquiring GPS...' : userLocation ? 'GPS Fixed' : 'My Location'}
        </button>
      </div>

      <div style={{ flex: 1, display: 'grid', gridTemplateColumns: '220px 1fr', gap: 16, minHeight: 0 }}>
        {/* Layer panel */}
        <div className="card" style={{ padding: '14px', display: 'flex', flexDirection: 'column', gap: 14 }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 12 }}>
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
          </div>

          {/* Spatial PostGIS Info */}
          <div style={{ padding: '10px', background: 'rgba(255,255,255,0.03)', borderRadius: 8, border: '1px solid var(--clr-border)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.75rem', fontWeight: 600, color: 'var(--clr-text-primary)', marginBottom: 4 }}>
              <Radio size={13} color="#22c55e" />
              PostGIS ST_DWithin
            </div>
            <div style={{ fontSize: '0.7rem', color: 'var(--clr-text-muted)', lineHeight: 1.4 }}>
              {userLocation
                ? `Query radius: 10 km from [${userLocation[0].toFixed(4)}, ${userLocation[1].toFixed(4)}]`
                : 'Click "My Location" to run PostGIS nearby query around your device.'}
            </div>
          </div>

          <div style={{ marginTop: 'auto' }}>
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

        {/* Map Container */}
        <div className="map-container" style={{ position: 'relative' }}>
          <MapContainer center={[22.5726, 88.3639]} zoom={12} style={{ height: '100%', width: '100%' }}>
            <TileLayer
              url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
              attribution='&copy; CARTO'
            />

            <MapCenterController center={userLocation} />

            {/* 🔵 User Current Location */}
            {userLocation && (
              <>
                <Circle
                  center={userLocation}
                  radius={5000}
                  pathOptions={{ color: '#3b82f6', fillColor: '#3b82f6', fillOpacity: 0.08, weight: 1.5, dashArray: '4, 6' }}
                />
                <CircleMarker
                  center={userLocation}
                  radius={12}
                  pathOptions={{ color: '#ffffff', fillColor: '#2563eb', fillOpacity: 1, weight: 3 }}
                >
                  <Popup>
                    <strong>🔵 Your Current Location</strong><br />
                    Lat: {userLocation[0].toFixed(5)}<br />
                    Lon: {userLocation[1].toFixed(5)}<br />
                    <em>PostGIS 5km Query Range active</em>
                  </Popup>
                </CircleMarker>
              </>
            )}

            {/* 🔥 Heatmap Zones */}
            {layers.heatmap && incidents.map(inc => (
              inc.latitude && inc.longitude ? (
                <Circle
                  key={`heat-${inc.id}`}
                  center={[inc.latitude, inc.longitude]}
                  radius={600}
                  pathOptions={{
                    color: inc.incident_type === 'WATERLOGGING' ? '#f97316' : inc.incident_type === 'TRAFFIC' ? '#eab308' : '#ef4444',
                    fillColor: inc.incident_type === 'WATERLOGGING' ? '#f97316' : inc.incident_type === 'TRAFFIC' ? '#eab308' : '#ef4444',
                    fillOpacity: 0.12,
                    weight: 1,
                  }}
                />
              ) : null
            ))}

            {/* 🚌 Buses */}
            {layers.buses && buses.map(bus =>
              bus.latitude && bus.longitude ? (
                <CircleMarker key={bus.id} center={[bus.latitude, bus.longitude]} radius={10} color="#3b82f6" fillColor="#3b82f6" fillOpacity={0.85}>
                  <Popup><strong>🚌 {bus.bus_number}</strong><br />{bus.route_name}<br />Status: {bus.status}<br />Speed: {bus.speed ?? '—'} km/h</Popup>
                </CircleMarker>
              ) : null
            )}

            {/* 🔴 Potholes */}
            {layers.potholes && potholes.map(d => (
              <CircleMarker key={d.id} center={[d.latitude, d.longitude]} radius={8} color="#ef4444" fillColor="#ef4444" fillOpacity={0.8}>
                <Popup>🕳️ <strong>Pothole / Road Defect</strong><br />Severity: {d.severity}<br />Conf: {confidencePct(d.confidence)}<br />{formatRelative(d.detected_at)}</Popup>
              </CircleMarker>
            ))}

            {/* 🟠 Waterlogging */}
            {layers.waterlogging && waterlogging.map(d => (
              <CircleMarker key={d.id} center={[d.latitude, d.longitude]} radius={9} color="#f97316" fillColor="#f97316" fillOpacity={0.8}>
                <Popup>💧 <strong>Waterlogging Hazard</strong><br />Severity: {d.severity}<br />Conf: {confidencePct(d.confidence)}</Popup>
              </CircleMarker>
            ))}

            {/* 🟡 Traffic */}
            {layers.traffic && trafficIncidents.map(inc => (
              <CircleMarker key={inc.id} center={[inc.latitude, inc.longitude]} radius={9} color="#eab308" fillColor="#eab308" fillOpacity={0.85}>
                <Popup>🟡 <strong>Traffic Jam / Congestion</strong><br />Priority: {inc.priority}<br />Status: {inc.status}</Popup>
              </CircleMarker>
            ))}

            {/* 🚨 Other Critical Incidents */}
            {layers.incidents && otherIncidents.map(inc => (
              <CircleMarker key={inc.id} center={[inc.latitude, inc.longitude]} radius={10} color="#dc2626" fillColor="#dc2626" fillOpacity={0.85}>
                <Popup>🚨 <strong>{inc.incident_type.replace(/_/g, ' ')}</strong><br />Priority: {inc.priority}<br />Status: {inc.status}</Popup>
              </CircleMarker>
            ))}

            {/* 📍 Detections */}
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
