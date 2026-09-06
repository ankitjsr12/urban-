import 'dart:io' show Platform;
import 'package:flutter/foundation.dart' show kIsWeb;

/// Application-wide constants and configuration.
/// Override via environment variables / build-time config in production.
class AppConfig {
  AppConfig._();

  /// Base URL for the FastAPI backend REST API.
  /// Set via --dart-define=API_BASE_URL=https://... at build time.
  static String get apiBaseUrl {
    const fromEnv = String.fromEnvironment('API_BASE_URL', defaultValue: '');
    if (fromEnv.isNotEmpty) return fromEnv;
    if (!kIsWeb && Platform.isAndroid) {
      return 'http://10.0.2.2:8000';
    }
    return 'http://localhost:8000';
  }

  /// WebSocket base URL.
  static String get wsBaseUrl {
    const fromEnv = String.fromEnvironment('WS_BASE_URL', defaultValue: '');
    if (fromEnv.isNotEmpty) return fromEnv;
    if (!kIsWeb && Platform.isAndroid) {
      return 'ws://10.0.2.2:8000';
    }
    return 'ws://localhost:8000';
  }

  /// When true, use mock data instead of real API calls.
  static const bool mockMode =
      bool.fromEnvironment('MOCK_MODE', defaultValue: false);

  // GPS settings
  static const int gpsIntervalMs = 5000;      // 5 seconds
  static const double gpsDistanceMeters = 20; // 20m movement threshold
  static const int locationAccuracyMeters = 10;

  // Upload settings
  static const int maxEvidenceSizeBytes = 50 * 1024 * 1024; // 50 MB
  static const int syncRetryDelayMs = 5000;

  // ANPR confidence threshold (matches backend ANPR_MIN_VERIFIED_CONFIDENCE=0.85)
  static const double anprVerifiedThreshold = 0.85;

  // Kolkata center coordinates (default map center)
  static const double defaultLat = 22.5726;
  static const double defaultLon = 88.3639;
}
