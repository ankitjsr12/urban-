import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:sqflite/sqflite.dart';
import 'package:path/path.dart' as p;
import 'dart:convert';

final localDatabaseProvider = Provider<LocalDatabase>((ref) => LocalDatabase());

/// Offline queue for GPS events, detections, incidents.
/// Each pending event is flushed via POST /api/v1/sync when network is restored.
class LocalDatabase {
  Database? _db;

  Future<Database> get db async {
    _db ??= await _open();
    return _db!;
  }

  Future<Database> _open() async {
    final path = p.join(await getDatabasesPath(), 'urbansense.db');
    return openDatabase(
      path,
      version: 1,
      onCreate: (db, version) async {
        await db.execute('''
          CREATE TABLE pending_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_event_id TEXT UNIQUE NOT NULL,
            event_type TEXT NOT NULL,
            payload TEXT NOT NULL,
            synced INTEGER DEFAULT 0,
            created_at INTEGER NOT NULL
          )
        ''');
        await db.execute('''
          CREATE INDEX idx_synced ON pending_events (synced)
        ''');
      },
    );
  }

  /// Insert an event to be synced later.
  Future<void> insertPendingEvent({
    required String clientEventId,
    required String eventType,
    required Map<String, dynamic> payload,
  }) async {
    final database = await db;
    await database.insert(
      'pending_events',
      {
        'client_event_id': clientEventId,
        'event_type': eventType,
        'payload': jsonEncode(payload),
        'synced': 0,
        'created_at': DateTime.now().millisecondsSinceEpoch,
      },
      conflictAlgorithm: ConflictAlgorithm.ignore,
    );
  }

  /// Fetch all unsynced events.
  Future<List<Map<String, dynamic>>> getPendingEvents() async {
    final database = await db;
    final rows = await database.query(
      'pending_events',
      where: 'synced = 0',
      orderBy: 'created_at ASC',
      limit: 100,
    );
    return rows.map((r) => {
      'client_event_id': r['client_event_id'],
      'event_type': r['event_type'],
      ...jsonDecode(r['payload'] as String) as Map<String, dynamic>,
    }).toList();
  }

  /// Mark events as synced.
  Future<void> markSynced(List<String> clientEventIds) async {
    if (clientEventIds.isEmpty) return;
    final database = await db;
    final placeholders = List.filled(clientEventIds.length, '?').join(',');
    await database.rawUpdate(
      'UPDATE pending_events SET synced = 1 WHERE client_event_id IN ($placeholders)',
      clientEventIds,
    );
  }

  /// Count unsynced events.
  Future<int> pendingCount() async {
    final database = await db;
    final result = await database.rawQuery('SELECT COUNT(*) as c FROM pending_events WHERE synced = 0');
    return result.first['c'] as int;
  }

  // ── Convenience helpers for detections / incidents ───────────────────────

  /// Insert a detection/incident event as a pending event.
  Future<void> insertDetection({
    required String busId,
    required String detectionType,
    required double confidence,
    required double latitude,
    required double longitude,
    Map<String, dynamic>? metadata,
  }) async {
    final id = DateTime.now().millisecondsSinceEpoch.toString();
    await insertPendingEvent(
      clientEventId: id,
      eventType: 'detection',
      payload: {
        'bus_id': busId,
        'detection_type': detectionType,
        'confidence': confidence,
        'latitude': latitude,
        'longitude': longitude,
        'timestamp': DateTime.now().toIso8601String(),
        if (metadata != null) ...metadata,
      },
    );
  }

  /// Fetch all detection/incident events (synced or not), for display.
  Future<List<Map<String, dynamic>>> getPendingDetections() async {
    final database = await db;
    final rows = await database.query(
      'pending_events',
      where: "event_type = 'detection'",
      orderBy: 'created_at DESC',
      limit: 100,
    );
    return rows.map((r) {
      final payload = jsonDecode(r['payload'] as String) as Map<String, dynamic>;
      return {
        'id': r['id'],
        'synced': r['synced'],
        'detection_type': payload['detection_type'] ?? 'OTHER',
        'timestamp': payload['timestamp'] ?? '',
        'latitude': payload['latitude'] ?? 0.0,
        'longitude': payload['longitude'] ?? 0.0,
        'confidence': payload['confidence'] ?? 0.0,
      };
    }).toList();
  }
}
