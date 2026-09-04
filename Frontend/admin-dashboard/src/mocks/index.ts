/**
 * Mock data layer — used only when VITE_MOCK_MODE=true
 * All data uses realistic Kolkata coordinates and enum values.
 * Replace with real API calls by setting VITE_MOCK_MODE=false.
 */

import type {
  User, TokenOut, Bus, Route, Detection, RoadDefect, TrafficEvent,
  Vehicle, Incident, AnalyticsOverview, HeatmapData,
} from '../models';

// Kolkata bounding box: lat 22.45–22.70, lon 88.25–88.45
function rndLat() { return 22.45 + Math.random() * 0.25; }
function rndLon() { return 88.25 + Math.random() * 0.20; }
function uuid() { return crypto.randomUUID(); }
function pastIso(minsAgo: number) {
  return new Date(Date.now() - minsAgo * 60_000).toISOString();
}

export function mockUser(): User {
  return { id: uuid(), name: 'Admin User', email: 'admin@urbansense.in', role: 'ADMIN', is_active: true };
}

export function mockToken(): TokenOut {
  return { access_token: 'mock-access-token', refresh_token: 'mock-refresh-token' };
}

const ROUTES: Route[] = [
  { id: uuid(), name: 'Barasat – Esplanade', code: 'R-01', origin: 'Barasat', destination: 'Esplanade' },
  { id: uuid(), name: 'Howrah – Salt Lake', code: 'R-02', origin: 'Howrah', destination: 'Salt Lake' },
  { id: uuid(), name: 'Garia – Park Street', code: 'R-03', origin: 'Garia', destination: 'Park Street' },
  { id: uuid(), name: 'Dunlop – Kalighat', code: 'R-04', origin: 'Dunlop', destination: 'Kalighat' },
];

export function mockRoutes(): Route[] { return ROUTES; }

const BUS_NUMBERS = ['BUS-101','BUS-102','BUS-103','BUS-104','BUS-105','BUS-106','BUS-107','BUS-108'];
const BUS_STATUSES = ['ACTIVE','ACTIVE','ACTIVE','ACTIVE','ACTIVE','INACTIVE','MAINTENANCE','OFFLINE'] as const;

export function mockBuses(): Bus[] {
  return BUS_NUMBERS.map((num, i) => ({
    id: uuid(),
    bus_number: num,
    registration_number: `WB14${1000 + i}`,
    route_id: ROUTES[i % ROUTES.length].id,
    driver_id: uuid(),
    status: BUS_STATUSES[i],
    created_at: pastIso(1440),
    updated_at: pastIso(i * 5),
    latitude: rndLat(),
    longitude: rndLon(),
    speed: BUS_STATUSES[i] === 'ACTIVE' ? Math.round(Math.random() * 60) : 0,
    last_update: pastIso(i),
    route_name: ROUTES[i % ROUTES.length].name,
  }));
}

const DETECTION_TYPES = [
  'POTHOLE','DAMAGED_ROAD','WATERLOGGING','TRAFFIC_SIGN','ZEBRA_CROSSING',
  'ROAD_DIVIDER','VEHICLE','PEDESTRIAN','CHILD_RISK','TRAFFIC_HAZARD',
] as const;

export function mockDetections(): Detection[] {
  return Array.from({ length: 20 }, (_, i) => ({
    id: uuid(),
    bus_id: uuid(),
    detection_type: DETECTION_TYPES[i % DETECTION_TYPES.length],
    confidence: 0.75 + Math.random() * 0.24,
    latitude: rndLat(),
    longitude: rndLon(),
    timestamp: pastIso(i * 3),
    frame_number: i * 30,
    evidence_id: null,
    model_name: 'yolov8-urban',
    model_version: '1.2.0',
    metadata: {},
    created_at: pastIso(i * 3),
    updated_at: pastIso(i * 3),
  }));
}

const DEFECT_TYPES = ['POTHOLE','WATERLOGGING','DAMAGED_ROAD','MISSING_SIGN','ZEBRA_CROSSING_ISSUE'];
const SEVERITIES = ['LOW','MEDIUM','HIGH','CRITICAL'];
const DEFECT_STATUSES = ['DETECTED','VERIFIED','ASSIGNED','IN_PROGRESS','RESOLVED','REJECTED'] as const;

export function mockDefects(): RoadDefect[] {
  return Array.from({ length: 20 }, (_, i) => ({
    id: uuid(),
    defect_type: DEFECT_TYPES[i % DEFECT_TYPES.length],
    severity: SEVERITIES[i % SEVERITIES.length],
    confidence: 0.7 + Math.random() * 0.29,
    latitude: rndLat(),
    longitude: rndLon(),
    bus_id: uuid(),
    evidence_id: null,
    status: DEFECT_STATUSES[i % DEFECT_STATUSES.length],
    detected_at: pastIso(i * 10),
    created_at: pastIso(i * 10),
    updated_at: pastIso(i * 5),
  }));
}

const DENSITIES = ['LOW','MEDIUM','HIGH','CRITICAL'] as const;

export function mockTrafficEvents(): TrafficEvent[] {
  return Array.from({ length: 24 }, (_, i) => {
    const cars = 20 + Math.round(Math.random() * 80);
    const bikes = 30 + Math.round(Math.random() * 120);
    const buses = 2 + Math.round(Math.random() * 10);
    const trucks = 1 + Math.round(Math.random() * 15);
    const autos = 5 + Math.round(Math.random() * 30);
    return {
      id: uuid(),
      cars, bikes, buses, trucks, autos,
      total_vehicles: cars + bikes + buses + trucks + autos,
      traffic_density: DENSITIES[i % DENSITIES.length],
      average_speed: 15 + Math.random() * 50,
      latitude: rndLat(),
      longitude: rndLon(),
      timestamp: pastIso(i * 60),
    };
  });
}

const VEHICLE_TYPES = ['CAR','BUS','TRUCK','MOTORCYCLE','AUTO','BICYCLE'] as const;

export function mockVehicles(): Vehicle[] {
  return Array.from({ length: 15 }, (_, i) => ({
    id: uuid(),
    vehicle_type: VEHICLE_TYPES[i % VEHICLE_TYPES.length],
    tracking_id: `TRK-${1000 + i}`,
    plate_number: i % 5 === 0 ? null : `WB${10 + i}AB${1000 + i}`,
    ocr_confidence: i % 5 === 0 ? null : 0.6 + Math.random() * 0.39,
    ocr_status: i % 5 === 0 ? null : i % 3 === 0 ? 'NEEDS_VERIFICATION' : 'VERIFIED',
  }));
}

const INCIDENT_TYPES = [
  'POSSIBLE_HIT_AND_RUN','DANGEROUS_DRIVING','COLLISION_LIKE_EVENT',
  'PEDESTRIAN_RISK','ROAD_HAZARD','OTHER',
] as const;
const PRIORITIES = ['LOW','MEDIUM','HIGH','CRITICAL'] as const;
const INCIDENT_STATUSES = ['NEW','UNDER_REVIEW','VERIFIED','ASSIGNED','RESOLVED','REJECTED'] as const;

export function mockIncidents(): Incident[] {
  return Array.from({ length: 17 }, (_, i) => ({
    id: uuid(),
    bus_id: uuid(),
    incident_type: INCIDENT_TYPES[i % INCIDENT_TYPES.length],
    priority: PRIORITIES[i % PRIORITIES.length],
    description: `Incident detected on route at ${rndLat().toFixed(4)}, ${rndLon().toFixed(4)}`,
    latitude: rndLat(),
    longitude: rndLon(),
    timestamp: pastIso(i * 15),
    vehicle_id: i % 3 === 0 ? uuid() : null,
    confidence: 0.72 + Math.random() * 0.27,
    status: INCIDENT_STATUSES[i % INCIDENT_STATUSES.length],
    created_by: uuid(),
    created_at: pastIso(i * 15),
    updated_at: pastIso(i * 5),
  }));
}

export function mockOverview(): AnalyticsOverview {
  return {
    total_buses: 128,
    active_buses: 94,
    total_detections: 8_432,
    total_road_defects: 342,
    total_incidents: 17,
    high_priority_incidents: 4,
    total_traffic_events: 1_245,
  };
}

export function mockHeatmap(kind: string): HeatmapData {
  const count = 50;
  return {
    type: 'FeatureCollection',
    features: Array.from({ length: count }, () => ({
      type: 'Feature' as const,
      geometry: { type: 'Point' as const, coordinates: [rndLon(), rndLat()] as [number, number] },
      properties: { kind },
    })),
  };
}
