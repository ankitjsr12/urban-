/// All backend REST API endpoint paths.
/// Never hard-code these inside individual screens.
class ApiEndpoints {
  ApiEndpoints._();

  // Auth
  static const String login    = '/api/v1/auth/login';
  static const String register = '/api/v1/auth/register';
  static const String me       = '/api/v1/auth/me';

  // Fleet
  static const String buses    = '/api/v1/buses';
  static String busLocation(String busId) => '/api/v1/buses/$busId/location';
  static String busLocationHistory(String busId) => '/api/v1/buses/$busId/location-history';
  static const String routes   = '/api/v1/routes';

  // Telemetry
  static const String locations       = '/api/v1/locations';
  static const String locationsNearby = '/api/v1/locations/nearby';
  static const String detections      = '/api/v1/detections';
  static const String roadDefects     = '/api/v1/road-defects';
  static const String roadDefectsNearby = '/api/v1/road-defects/nearby';
  static const String trafficEvents   = '/api/v1/traffic/events';
  static const String traffic         = '/api/v1/traffic';

  // Incidents
  static const String incidents       = '/api/v1/incidents';
  static const String incidentsNearby = '/api/v1/incidents/nearby';
  static String incidentStatus(String id) => '/api/v1/incidents/$id/status';

  // Evidence
  static const String evidenceUpload = '/api/v1/evidence/upload';

  // Vehicles
  static const String vehicles = '/api/v1/vehicles';

  // Reports
  static const String reports   = '/api/v1/reports';
  static const String myReports = '/api/v1/reports/my';

  // Sync
  static const String sync = '/api/v1/sync';

  // Analytics
  static const String analyticsOverview = '/api/v1/analytics/overview';
  static const String analyticsHeatmap  = '/api/v1/analytics/heatmap';

  // WebSocket channels
  static const String wsBuses      = '/live/buses';
  static const String wsIncidents  = '/live/incidents';
  static const String wsDetections = '/live/detections';
  static const String wsTraffic    = '/live/traffic';
}
