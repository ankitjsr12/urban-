import 'dart:async';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:geolocator/geolocator.dart';
import 'package:uuid/uuid.dart';
import '../core/constants/app_constants.dart';
import '../core/network/dio_client.dart';
import '../core/network/api_endpoints.dart';
import '../core/storage/local_database.dart';

final gpsServiceProvider = Provider<GpsService>((ref) {
  return GpsService(ref);
});

final currentPositionProvider = StateProvider<Position?>((ref) => null);
final gpsActiveProvider = StateProvider<bool>((ref) => false);

class GpsService {
  final Ref _ref;
  StreamSubscription<Position>? _subscription;
  final _uuid = const Uuid();

  GpsService(this._ref);

  Future<bool> requestPermission() async {
    bool serviceEnabled = await Geolocator.isLocationServiceEnabled();
    if (!serviceEnabled) return false;

    LocationPermission perm = await Geolocator.checkPermission();
    if (perm == LocationPermission.denied) {
      perm = await Geolocator.requestPermission();
      if (perm == LocationPermission.denied) return false;
    }
    if (perm == LocationPermission.deniedForever) return false;
    return true;
  }

  Future<void> startTracking({required String busId}) async {
    final granted = await requestPermission();
    if (!granted) return;

    _ref.read(gpsActiveProvider.notifier).state = true;

    final settings = LocationSettings(
      accuracy: LocationAccuracy.high,
      distanceFilter: AppConfig.gpsDistanceMeters.toInt(),
    );

    _subscription = Geolocator.getPositionStream(locationSettings: settings).listen(
      (position) => _onPosition(position, busId),
      onError: (e) => _ref.read(gpsActiveProvider.notifier).state = false,
    );
  }

  Future<void> _onPosition(Position position, String busId) async {
    _ref.read(currentPositionProvider.notifier).state = position;

    final clientEventId = _uuid.v4();
    final payload = {
      'bus_id': busId,
      'latitude': position.latitude,
      'longitude': position.longitude,
      'speed': position.speed * 3.6, // m/s → km/h
      'heading': position.heading,
      'accuracy': position.accuracy,
      'timestamp': position.timestamp.toIso8601String(),
      'client_event_id': clientEventId,
    };

    // Try live upload; if fails, queue locally
    try {
      if (!AppConfig.mockMode) {
        final client = _ref.read(dioClientProvider);
        await client.post<Map<String, dynamic>>(
          ApiEndpoints.locations,
          data: payload,
        );
      }
    } catch (_) {
      final localDb = _ref.read(localDatabaseProvider);
      await localDb.insertPendingEvent(
        clientEventId: clientEventId,
        eventType: 'location',
        payload: payload,
      );
    }
  }

  Future<void> stopTracking() async {
    await _subscription?.cancel();
    _subscription = null;
    _ref.read(gpsActiveProvider.notifier).state = false;
    _ref.read(currentPositionProvider.notifier).state = null;
  }

  Future<Position?> getCurrentPosition() async {
    try {
      return await Geolocator.getCurrentPosition(
        desiredAccuracy: LocationAccuracy.high,
      );
    } catch (_) {
      return null;
    }
  }
}
