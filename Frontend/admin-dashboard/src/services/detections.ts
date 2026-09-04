import { get, MOCK_MODE } from './api';
import type { Detection, RoadDefect, Vehicle, PagedResponse } from '../models';
import { mockDetections, mockDefects, mockVehicles } from '../mocks';

export async function getDetections(limit = 100, offset = 0): Promise<PagedResponse<Detection>> {
  if (MOCK_MODE) return { items: mockDetections(), total: 342, limit, offset };
  return get<PagedResponse<Detection>>(`/api/v1/detections?limit=${limit}&offset=${offset}`);
}

export async function getRoadDefects(limit = 100, offset = 0): Promise<PagedResponse<RoadDefect>> {
  if (MOCK_MODE) return { items: mockDefects(), total: 342, limit, offset };
  return get<PagedResponse<RoadDefect>>(`/api/v1/road-defects?limit=${limit}&offset=${offset}`);
}

export async function getVehicles(limit = 100, offset = 0): Promise<PagedResponse<Vehicle>> {
  if (MOCK_MODE) return { items: mockVehicles(), total: 58, limit, offset };
  return get<PagedResponse<Vehicle>>(`/api/v1/vehicles?limit=${limit}&offset=${offset}`);
}
