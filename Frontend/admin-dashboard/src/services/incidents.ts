import { get, patch, MOCK_MODE } from './api';
import type { Incident, PagedResponse } from '../models';
import { mockIncidents } from '../mocks';

export async function getIncidents(limit = 100, offset = 0): Promise<PagedResponse<Incident>> {
  if (MOCK_MODE) return { items: mockIncidents(), total: 17, limit, offset };
  return get<PagedResponse<Incident>>(`/api/v1/incidents?limit=${limit}&offset=${offset}`);
}

export async function patchIncidentStatus(incidentId: string, status: string): Promise<Incident> {
  return patch<Incident>(`/api/v1/incidents/${incidentId}/status`, { status });
}
