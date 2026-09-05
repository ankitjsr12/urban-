// Dart models matching the AI UrbanSense backend schemas exactly.

enum UserRole { ADMIN, AUTHORITY, DRIVER, CITIZEN }
enum BusStatus { ACTIVE, INACTIVE, MAINTENANCE, OFFLINE }
enum Density { LOW, MEDIUM, HIGH, CRITICAL }
enum Priority { LOW, MEDIUM, HIGH, CRITICAL }
enum IncidentStatus { NEW, UNDER_REVIEW, VERIFIED, ASSIGNED, RESOLVED, REJECTED }
enum IncidentType {
  POSSIBLE_HIT_AND_RUN,
  DANGEROUS_DRIVING,
  COLLISION_LIKE_EVENT,
  PEDESTRIAN_RISK,
  ROAD_HAZARD,
  OTHER,
}
enum DetectionType {
  POTHOLE,
  DAMAGED_ROAD,
  WATERLOGGING,
  TRAFFIC_SIGN,
  ZEBRA_CROSSING,
  ROAD_DIVIDER,
  VEHICLE,
  PEDESTRIAN,
  CHILD_RISK,
  TRAFFIC_HAZARD,
}
enum VehicleType { CAR, BUS, TRUCK, MOTORCYCLE, AUTO, BICYCLE, OTHER }

class User {
  final String id;
  final String name;
  final String email;
  final UserRole role;
  final bool isActive;

  const User({
    required this.id,
    required this.name,
    required this.email,
    required this.role,
    required this.isActive,
  });

  factory User.fromJson(Map<String, dynamic> j) => User(
    id: j['id'] as String,
    name: j['name'] as String,
    email: j['email'] as String,
    role: UserRole.values.firstWhere((e) => e.name == (j['role'] as String)),
    isActive: j['is_active'] as bool,
  );
}

class TokenOut {
  final String accessToken;
  final String refreshToken;
  const TokenOut({required this.accessToken, required this.refreshToken});

  factory TokenOut.fromJson(Map<String, dynamic> j) => TokenOut(
    accessToken: j['access_token'] as String,
    refreshToken: j['refresh_token'] as String,
  );
}

class Bus {
  final String id;
  final String busNumber;
  final String registrationNumber;
  final String? routeId;
  final String? driverId;
  final BusStatus status;

  const Bus({
    required this.id,
    required this.busNumber,
    required this.registrationNumber,
    this.routeId,
    this.driverId,
    required this.status,
  });

  factory Bus.fromJson(Map<String, dynamic> j) => Bus(
    id: j['id'] as String,
    busNumber: j['bus_number'] as String,
    registrationNumber: j['registration_number'] as String,
    routeId: j['route_id'] as String?,
    driverId: j['driver_id'] as String?,
    status: BusStatus.values.firstWhere((e) => e.name == (j['status'] as String)),
  );
}

class BusLocation {
  final String id;
  final String busId;
  final double latitude;
  final double longitude;
  final double? speed;
  final double? heading;
  final double? accuracy;
  final DateTime timestamp;
  final String? clientEventId;

  const BusLocation({
    required this.id,
    required this.busId,
    required this.latitude,
    required this.longitude,
    this.speed,
    this.heading,
    this.accuracy,
    required this.timestamp,
    this.clientEventId,
  });

  factory BusLocation.fromJson(Map<String, dynamic> j) => BusLocation(
    id: j['id'] as String,
    busId: j['bus_id'] as String,
    latitude: (j['latitude'] as num).toDouble(),
    longitude: (j['longitude'] as num).toDouble(),
    speed: j['speed'] != null ? (j['speed'] as num).toDouble() : null,
    heading: j['heading'] != null ? (j['heading'] as num).toDouble() : null,
    accuracy: j['accuracy'] != null ? (j['accuracy'] as num).toDouble() : null,
    timestamp: DateTime.parse(j['timestamp'] as String),
    clientEventId: j['client_event_id'] as String?,
  );

  Map<String, dynamic> toJson() => {
    'bus_id': busId,
    'latitude': latitude,
    'longitude': longitude,
    if (speed != null) 'speed': speed,
    if (heading != null) 'heading': heading,
    if (accuracy != null) 'accuracy': accuracy,
    'timestamp': timestamp.toIso8601String(),
    if (clientEventId != null) 'client_event_id': clientEventId,
  };
}

class Detection {
  final String id;
  final String? busId;
  final DetectionType detectionType;
  final double confidence;
  final double? latitude;
  final double? longitude;
  final DateTime timestamp;
  final String modelName;
  final String modelVersion;

  const Detection({
    required this.id,
    this.busId,
    required this.detectionType,
    required this.confidence,
    this.latitude,
    this.longitude,
    required this.timestamp,
    required this.modelName,
    required this.modelVersion,
  });

  factory Detection.fromJson(Map<String, dynamic> j) => Detection(
    id: j['id'] as String,
    busId: j['bus_id'] as String?,
    detectionType: DetectionType.values.firstWhere((e) => e.name == (j['detection_type'] as String)),
    confidence: (j['confidence'] as num).toDouble(),
    latitude: j['latitude'] != null ? (j['latitude'] as num).toDouble() : null,
    longitude: j['longitude'] != null ? (j['longitude'] as num).toDouble() : null,
    timestamp: DateTime.parse(j['timestamp'] as String),
    modelName: j['model_name'] as String,
    modelVersion: j['model_version'] as String,
  );
}

class Incident {
  final String id;
  final String? busId;
  final IncidentType incidentType;
  final Priority priority;
  final String? description;
  final double latitude;
  final double longitude;
  final DateTime timestamp;
  final double? confidence;
  final IncidentStatus status;

  const Incident({
    required this.id,
    this.busId,
    required this.incidentType,
    required this.priority,
    this.description,
    required this.latitude,
    required this.longitude,
    required this.timestamp,
    this.confidence,
    required this.status,
  });

  factory Incident.fromJson(Map<String, dynamic> j) => Incident(
    id: j['id'] as String,
    busId: j['bus_id'] as String?,
    incidentType: IncidentType.values.firstWhere((e) => e.name == (j['incident_type'] as String)),
    priority: Priority.values.firstWhere((e) => e.name == (j['priority'] as String)),
    description: j['description'] as String?,
    latitude: (j['latitude'] as num).toDouble(),
    longitude: (j['longitude'] as num).toDouble(),
    timestamp: DateTime.parse(j['timestamp'] as String),
    confidence: j['confidence'] != null ? (j['confidence'] as num).toDouble() : null,
    status: IncidentStatus.values.firstWhere((e) => e.name == (j['status'] as String)),
  );
}

class RoadDefect {
  final String id;
  final String defectType;
  final String severity;
  final double confidence;
  final double latitude;
  final double longitude;
  final String? busId;
  final String status;
  final DateTime detectedAt;

  const RoadDefect({
    required this.id,
    required this.defectType,
    required this.severity,
    required this.confidence,
    required this.latitude,
    required this.longitude,
    this.busId,
    required this.status,
    required this.detectedAt,
  });

  factory RoadDefect.fromJson(Map<String, dynamic> j) => RoadDefect(
    id: j['id'] as String,
    defectType: j['defect_type'] as String,
    severity: j['severity'] as String,
    confidence: (j['confidence'] as num).toDouble(),
    latitude: (j['latitude'] as num).toDouble(),
    longitude: (j['longitude'] as num).toDouble(),
    busId: j['bus_id'] as String?,
    status: j['status'] as String,
    detectedAt: DateTime.parse(j['detected_at'] as String),
  );
}

/// Represents a mock AI detection result (used in camera overlay UI).
class AiDetectionResult {
  final DetectionType type;
  final double confidence;
  final DateTime timestamp;
  /// Bounding box as fractions of screen: [left, top, width, height]
  final List<double>? bbox;

  const AiDetectionResult({
    required this.type,
    required this.confidence,
    required this.timestamp,
    this.bbox,
  });
}
