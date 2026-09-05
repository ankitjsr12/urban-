// TypeScript models matching the AI UrbanSense backend schemas exactly

export type Role = 'ADMIN' | 'AUTHORITY' | 'DRIVER' | 'CITIZEN';
export type BusStatus = 'ACTIVE' | 'INACTIVE' | 'MAINTENANCE' | 'OFFLINE';
export type Density = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
export type Priority = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
export type IncidentStatus = 'NEW' | 'UNDER_REVIEW' | 'VERIFIED' | 'ASSIGNED' | 'RESOLVED' | 'REJECTED';
export type IncidentType =
  | 'POSSIBLE_HIT_AND_RUN'
  | 'DANGEROUS_DRIVING'
  | 'COLLISION_LIKE_EVENT'
  | 'PEDESTRIAN_RISK'
  | 'ROAD_HAZARD'
  | 'ACCIDENT'
  | 'WATERLOGGING'
  | 'TRAFFIC'
  | 'CONGESTION'
  | 'SECURITY'
  | 'FIRE'
  | 'MEDICAL'
  | 'OTHER';
export type DetectionType =
  | 'POTHOLE'
  | 'DAMAGED_ROAD'
  | 'WATERLOGGING'
  | 'TRAFFIC_SIGN'
  | 'ZEBRA_CROSSING'
  | 'ROAD_DIVIDER'
  | 'VEHICLE'
  | 'PEDESTRIAN'
  | 'CHILD_RISK'
  | 'TRAFFIC_HAZARD';
export type DefectStatus = 'DETECTED' | 'VERIFIED' | 'ASSIGNED' | 'IN_PROGRESS' | 'RESOLVED' | 'REJECTED';
export type VehicleType = 'CAR' | 'BUS' | 'TRUCK' | 'MOTORCYCLE' | 'AUTO' | 'BICYCLE' | 'OTHER';

export interface ApiEnvelope<T> {
  data: T;
}

export interface PagedResponse<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}

export interface User {
  id: string;
  name: string;
  email: string;
  role: Role;
  is_active: boolean;
}

export interface TokenOut {
  access_token: string;
  refresh_token: string;
}

export interface Bus {
  id: string;
  bus_number: string;
  registration_number: string;
  route_id: string | null;
  driver_id: string | null;
  status: BusStatus;
  created_at: string;
  updated_at: string;
  // enriched client-side via WS
  latitude?: number;
  longitude?: number;
  speed?: number;
  last_update?: string;
  route_name?: string;
}

export interface Route {
  id: string;
  name: string;
  code: string;
  origin: string | null;
  destination: string | null;
}

export interface BusLocation {
  id: string;
  bus_id: string;
  latitude: number;
  longitude: number;
  speed: number | null;
  heading: number | null;
  accuracy: number | null;
  timestamp: string;
  client_event_id: string | null;
}

export interface Detection {
  id: string;
  bus_id: string | null;
  detection_type: DetectionType;
  confidence: number;
  latitude: number | null;
  longitude: number | null;
  timestamp: string;
  frame_number: number | null;
  evidence_id: string | null;
  model_name: string;
  model_version: string;
  metadata: Record<string, unknown>;
  created_at: string;
}

export interface RoadDefect {
  id: string;
  defect_type: string;
  severity: string;
  confidence: number;
  latitude: number;
  longitude: number;
  bus_id: string | null;
  evidence_id: string | null;
  status: DefectStatus;
  detected_at: string;
  created_at: string;
}

export interface TrafficEvent {
  id: string;
  cars: number;
  bikes: number;
  buses: number;
  trucks: number;
  autos: number;
  total_vehicles: number;
  traffic_density: Density;
  average_speed: number | null;
  latitude: number;
  longitude: number;
  timestamp: string;
}

export interface Vehicle {
  id: string;
  vehicle_type: VehicleType;
  tracking_id: string | null;
  plate_number: string | null;
  ocr_confidence: number | null;
  ocr_status: string | null;
}

export interface Incident {
  id: string;
  bus_id: string | null;
  incident_type: IncidentType;
  priority: Priority;
  description: string | null;
  latitude: number;
  longitude: number;
  timestamp: string;
  vehicle_id: string | null;
  confidence: number | null;
  status: IncidentStatus;
  created_by: string;
  created_at: string;
  updated_at: string;
}

export interface AnalyticsOverview {
  total_buses: number;
  active_buses: number;
  total_detections: number;
  total_road_defects: number;
  total_incidents: number;
  high_priority_incidents: number;
  total_traffic_events: number;
}

export interface HeatmapFeature {
  type: 'Feature';
  geometry: { type: 'Point'; coordinates: [number, number] };
  properties: { kind: string };
}

export interface HeatmapData {
  type: 'FeatureCollection';
  features: HeatmapFeature[];
}
