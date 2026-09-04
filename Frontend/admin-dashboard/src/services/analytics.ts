import { get, MOCK_MODE } from './api';
import type { AnalyticsOverview, HeatmapData } from '../models';
import { mockOverview, mockHeatmap } from '../mocks';

export async function getOverview(): Promise<AnalyticsOverview> {
  if (MOCK_MODE) return mockOverview();
  return get<AnalyticsOverview>('/api/v1/analytics/overview');
}

export async function getHeatmap(kind = 'incidents'): Promise<HeatmapData> {
  if (MOCK_MODE) return mockHeatmap(kind);
  return get<HeatmapData>(`/api/v1/analytics/heatmap?kind=${kind}`);
}
