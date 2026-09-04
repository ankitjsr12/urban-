import { get, MOCK_MODE } from './api';
import type { Bus, BusLocation, Route, PagedResponse } from '../models';
import { mockBuses, mockRoutes } from '../mocks';

export async function getBuses(limit = 100, offset = 0): Promise<PagedResponse<Bus>> {
  if (MOCK_MODE) return { items: mockBuses(), total: 8, limit, offset };
  return get<PagedResponse<Bus>>(`/api/v1/buses?limit=${limit}&offset=${offset}`);
}

export async function getRoutes(limit = 100, offset = 0): Promise<PagedResponse<Route>> {
  if (MOCK_MODE) return { items: mockRoutes(), total: 4, limit, offset };
  return get<PagedResponse<Route>>(`/api/v1/routes?limit=${limit}&offset=${offset}`);
}

export async function getBusLocation(busId: string): Promise<BusLocation | null> {
  if (MOCK_MODE) return null;
  return get<BusLocation | null>(`/api/v1/buses/${busId}/location`);
}

export async function getBusLocationHistory(busId: string, limit = 100): Promise<PagedResponse<BusLocation>> {
  if (MOCK_MODE) return { items: [], total: 0, limit, offset: 0 };
  return get<PagedResponse<BusLocation>>(`/api/v1/buses/${busId}/location-history?limit=${limit}`);
}
