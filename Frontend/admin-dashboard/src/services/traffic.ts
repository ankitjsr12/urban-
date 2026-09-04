import { get, MOCK_MODE } from './api';
import type { TrafficEvent, PagedResponse } from '../models';
import { mockTrafficEvents } from '../mocks';

export async function getTrafficEvents(limit = 100, offset = 0): Promise<PagedResponse<TrafficEvent>> {
  if (MOCK_MODE) return { items: mockTrafficEvents(), total: 1245, limit, offset };
  return get<PagedResponse<TrafficEvent>>(`/api/v1/traffic?limit=${limit}&offset=${offset}`);
}
