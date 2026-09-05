import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../core/network/dio_client.dart';
import '../core/network/api_endpoints.dart';
import '../core/storage/local_database.dart';
import '../core/constants/app_constants.dart';

final syncServiceProvider = Provider<SyncService>((ref) => SyncService(ref));
final networkOnlineProvider = StateProvider<bool>((ref) => true);

/// Watches connectivity and flushes the offline event queue via POST /api/v1/sync.
class SyncService {
  final Ref _ref;
  bool _syncing = false;

  SyncService(this._ref) {
    Connectivity().onConnectivityChanged.listen(_onConnectivityChange);
  }

  void _onConnectivityChange(List<ConnectivityResult> results) {
    final online = results.any((r) => r != ConnectivityResult.none);
    _ref.read(networkOnlineProvider.notifier).state = online;
    if (online) flush();
  }

  Future<bool> isOnline() async {
    final results = await Connectivity().checkConnectivity();
    return results.any((r) => r != ConnectivityResult.none);
  }

  /// Flush all pending events to the backend bulk sync endpoint.
  Future<void> flush() async {
    if (_syncing || AppConfig.mockMode) return;
    final localDb = _ref.read(localDatabaseProvider);
    final count = await localDb.pendingCount();
    if (count == 0) return;

    _syncing = true;
    try {
      final events = await localDb.getPendingEvents();
      if (events.isEmpty) return;

      final client = _ref.read(dioClientProvider);
      final result = await client.post<Map<String, dynamic>>(
        ApiEndpoints.sync,
        data: events,
      );

      final results = (result['results'] as List?)
          ?.cast<Map<String, dynamic>>() ?? [];
      final synced = results
          .where((r) => r['accepted'] == true)
          .map((r) => r['client_event_id'] as String)
          .toList();

      await localDb.markSynced(synced);
    } catch (_) {
      // Will retry on next connectivity change
    } finally {
      _syncing = false;
    }
  }
}
