import 'dart:math' as math;
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';
import '../../../services/gps_service.dart';
import '../../../core/constants/app_constants.dart';
import '../../../core/network/dio_client.dart';
import '../../../core/network/api_endpoints.dart';
import '../../../core/storage/local_database.dart';

/// Live Map screen with driver bus tracking, GPS location fix,
/// and PostGIS nearby incident/hazard markers with filter layers.
class LiveMapScreen extends ConsumerStatefulWidget {
  const LiveMapScreen({super.key});

  @override
  ConsumerState<LiveMapScreen> createState() => _LiveMapScreenState();
}

/// Alias for LiveMapScreen
typedef MapScreen = LiveMapScreen;

class _LiveMapScreenState extends ConsumerState<LiveMapScreen>
    with SingleTickerProviderStateMixin {
  final MapController _mapController = MapController();
  late final AnimationController _pulseController;

  List<Map<String, dynamic>> _nearbyIncidents = [];
  List<Map<String, dynamic>> _nearbyDefects = [];
  List<Map<String, dynamic>> _localDetections = [];

  bool _isLoadingNearby = false;
  bool _filterPotholes = true;
  bool _filterWaterlogging = true;
  bool _filterTraffic = true;
  bool _filterIncidents = true;
  bool _showHeatmap = true;

  @override
  void initState() {
    super.initState();
    _pulseController = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 2),
    )..repeat(reverse: true);

    _initGpsAndNearby();
  }

  @override
  void dispose() {
    _pulseController.dispose();
    super.dispose();
  }

  Future<void> _initGpsAndNearby() async {
    await _loadLocalMarkers();

    final gps = ref.read(gpsServiceProvider);
    final pos = await gps.getCurrentPosition();
    if (pos != null) {
      ref.read(currentPositionProvider.notifier).state = pos;
      await _fetchNearby(pos.latitude, pos.longitude);
    } else {
      // Fetch for default city center
      await _fetchNearby(AppConfig.defaultLat, AppConfig.defaultLon);
    }
  }

  Future<void> _loadLocalMarkers() async {
    try {
      final db = ref.read(localDatabaseProvider);
      final detections = await db.getPendingDetections();
      if (mounted) {
        setState(() {
          _localDetections = detections;
        });
      }
    } catch (_) {}
  }

  Future<void> _fetchNearby(double lat, double lon) async {
    if (!mounted) return;
    setState(() => _isLoadingNearby = true);

    try {
      final dio = ref.read(dioClientProvider);

      // Fetch nearby incidents from PostGIS endpoint
      try {
        final incData = await dio.get<Map<String, dynamic>>(
          ApiEndpoints.incidentsNearby,
          params: {'latitude': lat, 'longitude': lon, 'radius_km': 10.0, 'limit': 100},
        );
        final items = (incData['items'] as List?)?.cast<Map<String, dynamic>>() ?? [];
        if (mounted) {
          setState(() {
            _nearbyIncidents = items;
          });
        }
      } catch (_) {}

      // Fetch nearby road defects (potholes, waterlogging, etc.)
      try {
        final defData = await dio.get<Map<String, dynamic>>(
          ApiEndpoints.roadDefectsNearby,
          params: {'latitude': lat, 'longitude': lon, 'radius_km': 10.0, 'limit': 100},
        );
        final items = (defData['items'] as List?)?.cast<Map<String, dynamic>>() ?? [];
        if (mounted) {
          setState(() {
            _nearbyDefects = items;
          });
        }
      } catch (_) {}
    } finally {
      if (mounted) {
        setState(() => _isLoadingNearby = false);
      }
    }
  }

  Future<void> _onMyLocationPressed() async {
    final gps = ref.read(gpsServiceProvider);
    final granted = await gps.requestPermission();
    if (!granted) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Location permission is required to center on your position.'),
            backgroundColor: Color(0xFFEF4444),
          ),
        );
      }
      return;
    }

    final pos = await gps.getCurrentPosition();
    if (pos != null && mounted) {
      ref.read(currentPositionProvider.notifier).state = pos;
      _mapController.move(LatLng(pos.latitude, pos.longitude), 15.5);
      await _fetchNearby(pos.latitude, pos.longitude);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              'Location acquired: ${pos.latitude.toStringAsFixed(4)}, ${pos.longitude.toStringAsFixed(4)} (${_nearbyIncidents.length + _nearbyDefects.length} hazards nearby)',
            ),
            duration: const Duration(seconds: 2),
            backgroundColor: const Color(0xFF2563EB),
          ),
        );
      }
    } else {
      _mapController.move(const LatLng(AppConfig.defaultLat, AppConfig.defaultLon), 14.5);
    }
  }

  void _showHazardDetails({
    required String title,
    required String type,
    required String severity,
    required double lat,
    required double lon,
    String? distanceKm,
    String? status,
    String? description,
    Color? accentColor,
  }) {
    showModalBottomSheet(
      context: context,
      backgroundColor: const Color(0xFF111827),
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (ctx) {
        final color = accentColor ?? const Color(0xFFEF4444);
        return SafeArea(
          child: Padding(
            padding: const EdgeInsets.all(20),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Center(
                  child: Container(
                    width: 40,
                    height: 4,
                    decoration: BoxDecoration(
                      color: const Color(0xFF374151),
                      borderRadius: BorderRadius.circular(2),
                    ),
                  ),
                ),
                const SizedBox(height: 16),
                Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.all(10),
                      decoration: BoxDecoration(
                        color: color.withValues(alpha: 0.15),
                        shape: BoxShape.circle,
                        border: Border.all(color: color.withValues(alpha: 0.4)),
                      ),
                      child: Icon(
                        type == 'WATERLOGGING'
                            ? Icons.water_drop_rounded
                            : type == 'TRAFFIC'
                                ? Icons.traffic_rounded
                                : type == 'POTHOLE' || type == 'ROAD_HAZARD'
                                    ? Icons.warning_rounded
                                    : Icons.priority_high_rounded,
                        color: color,
                        size: 24,
                      ),
                    ),
                    const SizedBox(width: 14),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            title,
                            style: const TextStyle(
                              color: Colors.white,
                              fontSize: 16,
                              fontWeight: FontWeight.w700,
                            ),
                          ),
                          const SizedBox(height: 4),
                          Row(
                            children: [
                              Container(
                                padding: const EdgeInsets.symmetric(
                                    horizontal: 8, vertical: 2),
                                decoration: BoxDecoration(
                                  color: color.withValues(alpha: 0.2),
                                  borderRadius: BorderRadius.circular(6),
                                ),
                                child: Text(
                                  severity.toUpperCase(),
                                  style: TextStyle(
                                    color: color,
                                    fontSize: 11,
                                    fontWeight: FontWeight.w700,
                                  ),
                                ),
                              ),
                              if (distanceKm != null) ...[
                                const SizedBox(width: 8),
                                Text(
                                  '$distanceKm km away',
                                  style: const TextStyle(
                                    color: Color(0xFF9CA3AF),
                                    fontSize: 12,
                                  ),
                                ),
                              ],
                              if (status != null) ...[
                                const SizedBox(width: 8),
                                Text(
                                  '•  $status',
                                  style: const TextStyle(
                                    color: Color(0xFF22C55E),
                                    fontSize: 12,
                                    fontWeight: FontWeight.w600,
                                  ),
                                ),
                              ],
                            ],
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
                if (description != null && description.isNotEmpty) ...[
                  const SizedBox(height: 14),
                  Text(
                    description,
                    style: const TextStyle(
                      color: Color(0xFFD1D5DB),
                      fontSize: 13,
                      height: 1.4,
                    ),
                  ),
                ],
                const SizedBox(height: 12),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                  decoration: BoxDecoration(
                    color: const Color(0xFF1F2937),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.location_on_outlined,
                          color: Color(0xFF9CA3AF), size: 16),
                      const SizedBox(width: 6),
                      Text(
                        '${lat.toStringAsFixed(5)}, ${lon.toStringAsFixed(5)} (PostGIS SRID 4326)',
                        style: const TextStyle(
                          color: Color(0xFF9CA3AF),
                          fontFamily: 'monospace',
                          fontSize: 12,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    final position = ref.watch(currentPositionProvider);
    final gpsActive = ref.watch(gpsActiveProvider);

    final center = position != null
        ? LatLng(position.latitude, position.longitude)
        : const LatLng(AppConfig.defaultLat, AppConfig.defaultLon);

    // Filter combined list of markers
    final List<Widget> mapLayers = [];

    // Base OSM tiles
    mapLayers.add(
      TileLayer(
        urlTemplate: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
        userAgentPackageName: 'in.urbansense.mobile',
      ),
    );

    // Heatmap / Hazard Zone Circles
    if (_showHeatmap) {
      final List<CircleMarker> heatCircles = [];

      // Current location accuracy radius ring
      if (position != null) {
        heatCircles.add(
          CircleMarker(
            point: LatLng(position.latitude, position.longitude),
            radius: math.max(position.accuracy, 25.0),
            useRadiusInMeter: true,
            color: const Color(0xFF3B82F6).withValues(alpha: 0.18),
            borderColor: const Color(0xFF3B82F6).withValues(alpha: 0.4),
            borderStrokeWidth: 1.5,
          ),
        );
      }

      // Incident impact circles
      for (final inc in _nearbyIncidents) {
        final lat = (inc['latitude'] as num?)?.toDouble();
        final lon = (inc['longitude'] as num?)?.toDouble();
        if (lat == null || lon == null) continue;
        final type = (inc['incident_type'] as String? ?? '').toUpperCase();
        Color zoneColor = const Color(0xFFEF4444);
        if (type == 'WATERLOGGING') zoneColor = const Color(0xFFF97316);
        if (type == 'TRAFFIC') zoneColor = const Color(0xFFEAB308);

        heatCircles.add(
          CircleMarker(
            point: LatLng(lat, lon),
            radius: 90,
            useRadiusInMeter: true,
            color: zoneColor.withValues(alpha: 0.14),
            borderColor: zoneColor.withValues(alpha: 0.35),
            borderStrokeWidth: 1.0,
          ),
        );
      }

      mapLayers.add(CircleLayer(circles: heatCircles));
    }

    // Interactive Markers
    final List<Marker> allMarkers = [];

    // 1. Nearby Road Defects (Potholes, Waterlogging, Road Damage)
    for (final def in _nearbyDefects) {
      final lat = (def['latitude'] as num?)?.toDouble();
      final lon = (def['longitude'] as num?)?.toDouble();
      if (lat == null || lon == null) continue;

      final type = (def['defect_type'] as String? ?? '').toUpperCase();
      final isPothole = type == 'POTHOLE' || type == 'CRACK' || type == 'ROAD_DAMAGE';
      final isWater = type == 'WATERLOGGING';

      if (isPothole && !_filterPotholes) continue;
      if (isWater && !_filterWaterlogging) continue;

      final Color markerColor =
          isWater ? const Color(0xFFF97316) : const Color(0xFFEF4444);

      allMarkers.add(
        Marker(
          point: LatLng(lat, lon),
          width: 38,
          height: 38,
          child: GestureDetector(
            onTap: () => _showHazardDetails(
              title: isWater ? 'Waterlogging Hazard' : 'Pothole / Road Defect',
              type: type,
              severity: def['severity'] as String? ?? 'MEDIUM',
              lat: lat,
              lon: lon,
              distanceKm: def['distance_km']?.toString(),
              status: def['status'] as String?,
              accentColor: markerColor,
            ),
            child: Container(
              decoration: BoxDecoration(
                color: markerColor,
                shape: BoxShape.circle,
                border: Border.all(color: Colors.white, width: 2),
                boxShadow: [
                  BoxShadow(
                    color: markerColor.withValues(alpha: 0.6),
                    blurRadius: 8,
                    spreadRadius: 1,
                  )
                ],
              ),
              child: Icon(
                isWater ? Icons.water_drop_rounded : Icons.warning_rounded,
                color: Colors.white,
                size: 20,
              ),
            ),
          ),
        ),
      );
    }

    // 2. Nearby Incidents (Traffic, Accidents, Hazards)
    for (final inc in _nearbyIncidents) {
      final lat = (inc['latitude'] as num?)?.toDouble();
      final lon = (inc['longitude'] as num?)?.toDouble();
      if (lat == null || lon == null) continue;

      final type = (inc['incident_type'] as String? ?? '').toUpperCase();
      final isTraffic = type == 'TRAFFIC' || type == 'CONGESTION';
      final isWater = type == 'WATERLOGGING';
      final isPothole = type == 'ROAD_HAZARD';

      if (isTraffic && !_filterTraffic) continue;
      if (isWater && !_filterWaterlogging) continue;
      if (isPothole && !_filterPotholes) continue;
      if (!isTraffic && !isWater && !isPothole && !_filterIncidents) continue;

      Color markerColor = const Color(0xFFDC2626); // 🔴 Red
      IconData icon = Icons.priority_high_rounded;

      if (isTraffic) {
        markerColor = const Color(0xFFEAB308); // 🟡 Yellow
        icon = Icons.traffic_rounded;
      } else if (isWater) {
        markerColor = const Color(0xFFF97316); // 🟠 Orange
        icon = Icons.water_drop_rounded;
      } else if (isPothole) {
        markerColor = const Color(0xFFEF4444); // 🔴 Red
        icon = Icons.warning_amber_rounded;
      }

      allMarkers.add(
        Marker(
          point: LatLng(lat, lon),
          width: 38,
          height: 38,
          child: GestureDetector(
            onTap: () => _showHazardDetails(
              title: inc['title'] as String? ?? '${type.replaceAll('_', ' ')} Alert',
              type: type,
              severity: (inc['severity'] ?? inc['priority'] ?? 'HIGH') as String,
              lat: lat,
              lon: lon,
              distanceKm: inc['distance_km']?.toString(),
              status: inc['status'] as String?,
              description: inc['description'] as String?,
              accentColor: markerColor,
            ),
            child: Container(
              decoration: BoxDecoration(
                color: markerColor,
                shape: BoxShape.circle,
                border: Border.all(color: Colors.white, width: 2),
                boxShadow: [
                  BoxShadow(
                    color: markerColor.withValues(alpha: 0.6),
                    blurRadius: 8,
                    spreadRadius: 1,
                  )
                ],
              ),
              child: Icon(icon, color: Colors.white, size: 20),
            ),
          ),
        ),
      );
    }

    // 3. Local Camera/ANPR Detections
    for (final loc in _localDetections) {
      final lat = (loc['latitude'] as num?)?.toDouble();
      final lon = (loc['longitude'] as num?)?.toDouble();
      if (lat == null || lon == null) continue;
      final type = (loc['detection_type'] as String? ?? '').toUpperCase();
      final isPothole = type == 'POTHOLE' || type == 'DAMAGED_ROAD';
      if (isPothole && !_filterPotholes) continue;

      allMarkers.add(
        Marker(
          point: LatLng(lat, lon),
          width: 32,
          height: 32,
          child: Container(
            decoration: BoxDecoration(
              color: const Color(0xFF10B981),
              shape: BoxShape.circle,
              border: Border.all(color: Colors.white, width: 2),
            ),
            child: const Icon(Icons.camera_alt_rounded, color: Colors.white, size: 16),
          ),
        ),
      );
    }

    // 4. 🔵 CURRENT LOCATION MARKER
    if (position != null) {
      allMarkers.add(
        Marker(
          point: LatLng(position.latitude, position.longitude),
          width: 52,
          height: 52,
          child: AnimatedBuilder(
            animation: _pulseController,
            builder: (context, child) {
              return Stack(
                alignment: Alignment.center,
                children: [
                  // Pulsing halo
                  Container(
                    width: 44 + (_pulseController.value * 8),
                    height: 44 + (_pulseController.value * 8),
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      color: const Color(0xFF3B82F6).withValues(alpha: 0.35 - (_pulseController.value * 0.2)),
                    ),
                  ),
                  // Solid blue outer ring
                  Container(
                    width: 36,
                    height: 36,
                    decoration: BoxDecoration(
                      color: const Color(0xFF2563EB),
                      shape: BoxShape.circle,
                      border: Border.all(color: Colors.white, width: 3),
                      boxShadow: const [
                        BoxShadow(
                          color: Color(0xFF1D4ED8),
                          blurRadius: 10,
                          spreadRadius: 2,
                        ),
                      ],
                    ),
                    child: const Icon(
                      Icons.navigation_rounded,
                      color: Colors.white,
                      size: 20,
                    ),
                  ),
                ],
              );
            },
          ),
        ),
      );
    }

    mapLayers.add(MarkerLayer(markers: allMarkers));

    return Scaffold(
      backgroundColor: const Color(0xFF0A0F1E),
      appBar: AppBar(
        backgroundColor: const Color(0xFF111827),
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_rounded, color: Colors.white),
          onPressed: () => Navigator.pop(context),
        ),
        title: const Text(
          'Live GIS Map & Hazards',
          style: TextStyle(color: Colors.white, fontWeight: FontWeight.w700),
        ),
        actions: [
          if (_isLoadingNearby)
            const Padding(
              padding: EdgeInsets.symmetric(horizontal: 12),
              child: Center(
                child: SizedBox(
                  width: 18,
                  height: 18,
                  child: CircularProgressIndicator(
                    strokeWidth: 2,
                    color: Color(0xFF3B82F6),
                  ),
                ),
              ),
            ),
          if (position != null)
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 10),
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 3),
                decoration: BoxDecoration(
                  color: const Color(0xFF22C55E).withValues(alpha: 0.15),
                  borderRadius: BorderRadius.circular(100),
                  border: Border.all(color: const Color(0xFF22C55E).withValues(alpha: 0.3)),
                ),
                child: Row(mainAxisSize: MainAxisSize.min, children: [
                  Container(
                    width: 6,
                    height: 6,
                    decoration: const BoxDecoration(
                      color: Color(0xFF22C55E),
                      shape: BoxShape.circle,
                    ),
                  ),
                  const SizedBox(width: 5),
                  Text(
                    '${(position.speed * 3.6).toStringAsFixed(0)} km/h',
                    style: const TextStyle(
                      color: Color(0xFF22C55E),
                      fontSize: 12,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                ]),
              ),
            ),
        ],
      ),
      body: Stack(
        children: [
          FlutterMap(
            mapController: _mapController,
            options: MapOptions(
              initialCenter: center,
              initialZoom: 14.5,
              interactionOptions: const InteractionOptions(
                flags: InteractiveFlag.all,
              ),
            ),
            children: mapLayers,
          ),

          // Layer filter chips
          Positioned(
            top: 12,
            left: 12,
            right: 12,
            child: SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              child: Row(
                children: [
                  FilterChip(
                    avatar: const Text('🔴', style: TextStyle(fontSize: 12)),
                    label: const Text('Potholes'),
                    selected: _filterPotholes,
                    onSelected: (v) => setState(() => _filterPotholes = v),
                    selectedColor: const Color(0xFFEF4444).withValues(alpha: 0.25),
                    checkmarkColor: const Color(0xFFEF4444),
                    backgroundColor: const Color(0xFF111827).withValues(alpha: 0.9),
                    labelStyle: TextStyle(
                      color: _filterPotholes ? const Color(0xFFEF4444) : const Color(0xFF9CA3AF),
                      fontSize: 12,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  const SizedBox(width: 6),
                  FilterChip(
                    avatar: const Text('🟠', style: TextStyle(fontSize: 12)),
                    label: const Text('Waterlogging'),
                    selected: _filterWaterlogging,
                    onSelected: (v) => setState(() => _filterWaterlogging = v),
                    selectedColor: const Color(0xFFF97316).withValues(alpha: 0.25),
                    checkmarkColor: const Color(0xFFF97316),
                    backgroundColor: const Color(0xFF111827).withValues(alpha: 0.9),
                    labelStyle: TextStyle(
                      color: _filterWaterlogging ? const Color(0xFFF97316) : const Color(0xFF9CA3AF),
                      fontSize: 12,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  const SizedBox(width: 6),
                  FilterChip(
                    avatar: const Text('🟡', style: TextStyle(fontSize: 12)),
                    label: const Text('Traffic'),
                    selected: _filterTraffic,
                    onSelected: (v) => setState(() => _filterTraffic = v),
                    selectedColor: const Color(0xFFEAB308).withValues(alpha: 0.25),
                    checkmarkColor: const Color(0xFFEAB308),
                    backgroundColor: const Color(0xFF111827).withValues(alpha: 0.9),
                    labelStyle: TextStyle(
                      color: _filterTraffic ? const Color(0xFFEAB308) : const Color(0xFF9CA3AF),
                      fontSize: 12,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  const SizedBox(width: 6),
                  FilterChip(
                    avatar: const Text('🚨', style: TextStyle(fontSize: 12)),
                    label: const Text('Incidents'),
                    selected: _filterIncidents,
                    onSelected: (v) => setState(() => _filterIncidents = v),
                    selectedColor: const Color(0xFFDC2626).withValues(alpha: 0.25),
                    checkmarkColor: const Color(0xFFDC2626),
                    backgroundColor: const Color(0xFF111827).withValues(alpha: 0.9),
                    labelStyle: TextStyle(
                      color: _filterIncidents ? const Color(0xFFDC2626) : const Color(0xFF9CA3AF),
                      fontSize: 12,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  const SizedBox(width: 6),
                  FilterChip(
                    avatar: const Text('🔥', style: TextStyle(fontSize: 12)),
                    label: const Text('Heatmap'),
                    selected: _showHeatmap,
                    onSelected: (v) => setState(() => _showHeatmap = v),
                    selectedColor: const Color(0xFF8B5CF6).withValues(alpha: 0.25),
                    checkmarkColor: const Color(0xFF8B5CF6),
                    backgroundColor: const Color(0xFF111827).withValues(alpha: 0.9),
                    labelStyle: TextStyle(
                      color: _showHeatmap ? const Color(0xFFA78BFA) : const Color(0xFF9CA3AF),
                      fontSize: 12,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ],
              ),
            ),
          ),

          // "My Location" Floating Action Button
          Positioned(
            right: 16,
            bottom: 105,
            child: FloatingActionButton.extended(
              heroTag: 'my_location_btn',
              backgroundColor: const Color(0xFF1E293B),
              foregroundColor: const Color(0xFF38BDF8),
              elevation: 4,
              onPressed: _onMyLocationPressed,
              icon: const Icon(Icons.my_location_rounded, size: 20),
              label: const Text(
                'My Location',
                style: TextStyle(fontSize: 12, fontWeight: FontWeight.w700),
              ),
            ),
          ),

          // GPS Info Bottom Bar
          Positioned(
            bottom: 20,
            left: 16,
            right: 16,
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
              decoration: BoxDecoration(
                color: const Color(0xFF111827).withValues(alpha: 0.95),
                borderRadius: BorderRadius.circular(14),
                border: Border.all(color: const Color(0xFF1E2D45)),
                boxShadow: const [
                  BoxShadow(
                    color: Colors.black45,
                    blurRadius: 10,
                    offset: Offset(0, 4),
                  ),
                ],
              ),
              child: Row(
                children: [
                  Icon(
                    position != null ? Icons.gps_fixed_rounded : Icons.gps_not_fixed_rounded,
                    color: position != null ? const Color(0xFF22C55E) : const Color(0xFF6B7280),
                    size: 20,
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Text(
                          position != null
                              ? '${position.latitude.toStringAsFixed(5)}, ${position.longitude.toStringAsFixed(5)}'
                              : (gpsActive ? 'Acquiring GPS fix…' : 'Tap "My Location" to center on device'),
                          style: const TextStyle(
                            color: Color(0xFFF3F4F6),
                            fontFamily: 'monospace',
                            fontSize: 12,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                        const SizedBox(height: 2),
                        Text(
                          '${_nearbyIncidents.length} incidents  ·  ${_nearbyDefects.length} road defects  ·  PostGIS radius 10km',
                          style: const TextStyle(color: Color(0xFF9CA3AF), fontSize: 11),
                        ),
                      ],
                    ),
                  ),
                  IconButton(
                    tooltip: 'Refresh Nearby Hazards',
                    icon: const Icon(Icons.refresh_rounded, color: Color(0xFF38BDF8), size: 20),
                    onPressed: () {
                      final lat = position?.latitude ?? AppConfig.defaultLat;
                      final lon = position?.longitude ?? AppConfig.defaultLon;
                      _fetchNearby(lat, lon);
                    },
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
