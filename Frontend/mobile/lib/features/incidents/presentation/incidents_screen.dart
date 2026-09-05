import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/storage/local_database.dart';
import '../../../core/network/dio_client.dart';
import '../../../core/network/api_endpoints.dart';
import '../../../core/constants/app_constants.dart';

/// Incident management screen — lists remote + local queued incidents with details and creation flow.
class IncidentsScreen extends ConsumerStatefulWidget {
  const IncidentsScreen({super.key});

  @override
  ConsumerState<IncidentsScreen> createState() => _IncidentsScreenState();
}

class _IncidentsScreenState extends ConsumerState<IncidentsScreen> {
  List<Map<String, dynamic>> _incidents = [];
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });

    try {
      final db = ref.read(localDatabaseProvider);
      final localRows = await db.getPendingDetections();

      if (!AppConfig.mockMode) {
        try {
          final client = ref.read(dioClientProvider);
          final res = await client.get<Map<String, dynamic>>(ApiEndpoints.incidents);
          final items = (res['items'] as List?)?.cast<Map<String, dynamic>>() ?? [];
          final remoteMapped = items.map((item) => {
            'id': item['id'],
            'detection_type': item['incident_type'] ?? 'INCIDENT',
            'severity': item['priority'] ?? 'MEDIUM',
            'timestamp': item['timestamp'] ?? item['created_at'] ?? '',
            'latitude': (item['latitude'] as num?)?.toDouble() ?? 0.0,
            'longitude': (item['longitude'] as num?)?.toDouble() ?? 0.0,
            'confidence': (item['confidence'] as num?)?.toDouble() ?? 1.0,
            'status': item['status'] ?? 'VERIFIED',
            'synced': 1,
            'description': item['description'] ?? '',
            'thumbnail_url': item['thumbnail_url'],
          }).toList();

          if (mounted) {
            setState(() {
              _incidents = [...localRows, ...remoteMapped];
              _loading = false;
            });
            return;
          }
        } catch (_) {
          // Fall back to local records if network call fails
        }
      }

      if (mounted) {
        setState(() {
          _incidents = localRows;
          _loading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _error = 'Failed to load incidents: $e';
          _loading = false;
        });
      }
    }
  }

  Future<void> _showCreateDialog() async {
    final type = await showDialog<String>(
      context: context,
      builder: (_) => const _IncidentTypeDialog(),
    );
    if (type == null || !mounted) return;
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: const Color(0xFF111827),
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(20))),
      builder: (_) => _IncidentFormSheet(incidentType: type, onSaved: _load),
    );
  }

  void _showDetailSheet(Map<String, dynamic> inc) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: const Color(0xFF111827),
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(20))),
      builder: (_) => _IncidentDetailSheet(incident: inc),
    );
  }

  Color _priorityColor(String type) {
    return switch (type.toUpperCase()) {
      'ACCIDENT' || 'HIT_AND_RUN' || 'CRITICAL' => const Color(0xFFEF4444),
      'RASH_DRIVING' || 'PEDESTRIAN_RISK' || 'HIGH' => const Color(0xFFF97316),
      'ROAD_HAZARD' || 'WATERLOGGING' || 'MEDIUM' => const Color(0xFFF59E0B),
      _ => const Color(0xFF22C55E),
    };
  }

  IconData _typeIcon(String type) {
    return switch (type.toUpperCase()) {
      'ACCIDENT' => Icons.car_crash_rounded,
      'HIT_AND_RUN' => Icons.directions_run_rounded,
      'RASH_DRIVING' => Icons.speed_rounded,
      'PEDESTRIAN_RISK' => Icons.directions_walk_rounded,
      'ROAD_HAZARD' => Icons.warning_amber_rounded,
      'WATERLOGGING' => Icons.water_drop_rounded,
      'TRAFFIC_CONGESTION' => Icons.traffic_rounded,
      _ => Icons.report_problem_rounded,
    };
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0A0F1E),
      appBar: AppBar(
        backgroundColor: const Color(0xFF111827),
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_rounded, color: Colors.white),
          onPressed: () => Navigator.pop(context),
        ),
        title: const Text('Incidents & Alerts', style: TextStyle(color: Colors.white, fontWeight: FontWeight.w700)),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh_rounded, color: Color(0xFF8FA3C0)),
            onPressed: _load,
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _showCreateDialog,
        backgroundColor: const Color(0xFFEF4444),
        icon: const Icon(Icons.add_alert_rounded),
        label: const Text('Report Incident', style: TextStyle(fontWeight: FontWeight.w700)),
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator(color: Color(0xFF3B82F6)))
          : _error != null
              ? Center(
                  child: Column(mainAxisSize: MainAxisSize.min, children: [
                    const Icon(Icons.error_outline_rounded, color: Color(0xFFEF4444), size: 48),
                    const SizedBox(height: 12),
                    Text(_error!, style: const TextStyle(color: Color(0xFF8FA3C0))),
                    const SizedBox(height: 16),
                    ElevatedButton(onPressed: _load, child: const Text('Retry')),
                  ]),
                )
              : _incidents.isEmpty
                  ? Center(
                      child: Column(mainAxisSize: MainAxisSize.min, children: [
                        const Icon(Icons.shield_rounded, color: Color(0xFF1E2D45), size: 80),
                        const SizedBox(height: 16),
                        const Text('No Incidents Logged',
                            style: TextStyle(color: Color(0xFF8FA3C0), fontSize: 18, fontWeight: FontWeight.w700)),
                        const SizedBox(height: 8),
                        const Text('Tap below to report a safety or road incident',
                            style: TextStyle(color: Color(0xFF4D6180))),
                        const SizedBox(height: 20),
                        ElevatedButton.icon(
                          onPressed: _showCreateDialog,
                          icon: const Icon(Icons.add_alert_rounded),
                          label: const Text('Report Incident'),
                          style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFFEF4444)),
                        ),
                      ]),
                    )
                  : RefreshIndicator(
                      onRefresh: _load,
                      child: ListView.builder(
                        padding: const EdgeInsets.fromLTRB(16, 16, 16, 80),
                        itemCount: _incidents.length,
                        itemBuilder: (_, i) {
                          final inc = _incidents[i];
                          final type = inc['detection_type'] as String? ?? 'OTHER';
                          final severity = inc['severity'] as String? ?? 'MEDIUM';
                          final color = _priorityColor(severity);
                          final synced = (inc['synced'] as int? ?? 0) == 1;
                          final ts = inc['timestamp'] as String? ?? '';
                          final lat = (inc['latitude'] as num?)?.toDouble() ?? 0.0;
                          final lon = (inc['longitude'] as num?)?.toDouble() ?? 0.0;
                          final status = inc['status'] as String? ?? (synced ? 'VERIFIED' : 'LOCAL');

                          return GestureDetector(
                            onTap: () => _showDetailSheet(inc),
                            child: Container(
                              margin: const EdgeInsets.only(bottom: 12),
                              padding: const EdgeInsets.all(14),
                              decoration: BoxDecoration(
                                color: const Color(0xFF111827),
                                borderRadius: BorderRadius.circular(14),
                                border: Border(left: BorderSide(color: color, width: 4)),
                              ),
                              child: Row(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  // Thumbnail / Preview Box
                                  Container(
                                    width: 52,
                                    height: 52,
                                    decoration: BoxDecoration(
                                      color: color.withOpacity(0.12),
                                      borderRadius: BorderRadius.circular(10),
                                      border: Border.all(color: color.withOpacity(0.3)),
                                    ),
                                    child: Center(
                                      child: Icon(_typeIcon(type), color: color, size: 26),
                                    ),
                                  ),
                                  const SizedBox(width: 12),

                                  // Incident Details
                                  Expanded(
                                    child: Column(
                                      crossAxisAlignment: CrossAxisAlignment.start,
                                      children: [
                                        Row(
                                          children: [
                                            Expanded(
                                              child: Text(
                                                type.replaceAll('_', ' '),
                                                style: const TextStyle(
                                                  color: Color(0xFFE8EDF5),
                                                  fontWeight: FontWeight.w700,
                                                  fontSize: 14,
                                                ),
                                              ),
                                            ),
                                            Container(
                                              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                                              decoration: BoxDecoration(
                                                color: color.withOpacity(0.15),
                                                borderRadius: BorderRadius.circular(4),
                                              ),
                                              child: Text(
                                                severity,
                                                style: TextStyle(
                                                  color: color,
                                                  fontSize: 10,
                                                  fontWeight: FontWeight.w700,
                                                ),
                                              ),
                                            ),
                                          ],
                                        ),
                                        const SizedBox(height: 4),
                                        Row(
                                          children: [
                                            const Icon(Icons.location_on_outlined, size: 12, color: Color(0xFF4D6180)),
                                            const SizedBox(width: 2),
                                            Text(
                                              '${lat.toStringAsFixed(4)}, ${lon.toStringAsFixed(4)}',
                                              style: const TextStyle(color: Color(0xFF8FA3C0), fontSize: 11, fontFamily: 'monospace'),
                                            ),
                                          ],
                                        ),
                                        const SizedBox(height: 4),
                                        Row(
                                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                          children: [
                                            Text(
                                              ts.length > 19 ? ts.substring(0, 19) : ts,
                                              style: const TextStyle(color: Color(0xFF4D6180), fontSize: 11),
                                            ),
                                            Container(
                                              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                                              decoration: BoxDecoration(
                                                color: (synced ? const Color(0xFF22C55E) : const Color(0xFFF59E0B)).withOpacity(0.15),
                                                borderRadius: BorderRadius.circular(4),
                                              ),
                                              child: Text(
                                                status,
                                                style: TextStyle(
                                                  color: synced ? const Color(0xFF22C55E) : const Color(0xFFF59E0B),
                                                  fontSize: 9,
                                                  fontWeight: FontWeight.w700,
                                                ),
                                              ),
                                            ),
                                          ],
                                        ),
                                      ],
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          );
                        },
                      ),
                    ),
    );
  }
}

class _IncidentDetailSheet extends StatelessWidget {
  final Map<String, dynamic> incident;
  const _IncidentDetailSheet({required this.incident});

  @override
  Widget build(BuildContext context) {
    final type = incident['detection_type'] as String? ?? 'OTHER';
    final severity = incident['severity'] as String? ?? 'MEDIUM';
    final timestamp = incident['timestamp'] as String? ?? '';
    final lat = (incident['latitude'] as num?)?.toDouble() ?? 0.0;
    final lon = (incident['longitude'] as num?)?.toDouble() ?? 0.0;
    final synced = (incident['synced'] as int? ?? 0) == 1;
    final desc = incident['description'] as String? ?? '';
    final status = incident['status'] as String? ?? (synced ? 'VERIFIED' : 'LOCAL_QUEUE');

    return Padding(
      padding: const EdgeInsets.all(24),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(children: [
            Expanded(
              child: Text(type.replaceAll('_', ' '),
                  style: const TextStyle(
                      color: Color(0xFFE8EDF5),
                      fontSize: 20,
                      fontWeight: FontWeight.w800)),
            ),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
              decoration: BoxDecoration(
                color: (synced ? const Color(0xFF22C55E) : const Color(0xFFF59E0B)).withOpacity(0.15),
                borderRadius: BorderRadius.circular(100),
              ),
              child: Text(status,
                  style: TextStyle(
                      color: synced ? const Color(0xFF22C55E) : const Color(0xFFF59E0B),
                      fontSize: 12,
                      fontWeight: FontWeight.w700)),
            ),
          ]),
          const SizedBox(height: 16),

          // Simulated Video / Evidence Thumbnail Preview Box
          Container(
            height: 140,
            width: double.infinity,
            decoration: BoxDecoration(
              color: const Color(0xFF0A0F1E),
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: const Color(0xFF1E2D45)),
            ),
            child: Stack(
              alignment: Alignment.center,
              children: [
                Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(Icons.videocam_rounded, color: const Color(0xFF3B82F6).withOpacity(0.8), size: 36),
                    const SizedBox(height: 6),
                    const Text('Captured Dashcam Evidence', style: TextStyle(color: Color(0xFF8FA3C0), fontSize: 12)),
                  ],
                ),
                Positioned(
                  bottom: 8,
                  right: 8,
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                    decoration: BoxDecoration(color: Colors.black.withOpacity(0.7), borderRadius: BorderRadius.circular(4)),
                    child: const Text('AI FLAGGED', style: TextStyle(color: Color(0xFF22C55E), fontSize: 10, fontWeight: FontWeight.bold)),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),

          _DetailRow(label: 'Severity', value: severity),
          _DetailRow(label: 'Time', value: timestamp.length > 19 ? timestamp.substring(0, 19) : timestamp),
          _DetailRow(label: 'Location', value: '${lat.toStringAsFixed(6)}, ${lon.toStringAsFixed(6)}'),
          if (desc.isNotEmpty) _DetailRow(label: 'Description', value: desc),
          const SizedBox(height: 24),
          SizedBox(
            width: double.infinity,
            child: ElevatedButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('Close'),
            ),
          ),
          const SizedBox(height: 12),
        ],
      ),
    );
  }
}

class _DetailRow extends StatelessWidget {
  final String label, value;
  const _DetailRow({required this.label, required this.value});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
        SizedBox(
            width: 100,
            child: Text(label, style: const TextStyle(color: Color(0xFF8FA3C0), fontSize: 13))),
        Expanded(
          child: Text(value,
              style: const TextStyle(
                  color: Color(0xFFE8EDF5),
                  fontSize: 13,
                  fontWeight: FontWeight.w600,
                  fontFamily: 'monospace')),
        ),
      ]),
    );
  }
}

class _IncidentTypeDialog extends StatelessWidget {
  const _IncidentTypeDialog();

  @override
  Widget build(BuildContext context) {
    const types = [
      ('ACCIDENT', '🚗 Traffic Accident'),
      ('HIT_AND_RUN', '🏃 Hit & Run Event'),
      ('RASH_DRIVING', '💨 Dangerous / Rash Driving'),
      ('PEDESTRIAN_RISK', '🚶 Pedestrian / Child Risk'),
      ('ROAD_HAZARD', '⚠️ Road Obstacle / Hazard'),
      ('WATERLOGGING', '💧 Road Waterlogging'),
      ('TRAFFIC_CONGESTION', '🚦 Heavy Traffic Congestion'),
      ('OTHER', '📌 Other Incident'),
    ];
    return AlertDialog(
      backgroundColor: const Color(0xFF111827),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      title: const Text('Select Incident Type',
          style: TextStyle(color: Color(0xFFE8EDF5), fontWeight: FontWeight.w700)),
      content: SizedBox(
        width: double.maxFinite,
        child: ListView(
          shrinkWrap: true,
          children: types
              .map((t) => ListTile(
                    title: Text(t.$2,
                        style: const TextStyle(
                            color: Color(0xFFE8EDF5), fontWeight: FontWeight.w600)),
                    onTap: () => Navigator.pop(context, t.$1),
                  ))
              .toList(),
        ),
      ),
    );
  }
}

class _IncidentFormSheet extends ConsumerStatefulWidget {
  final String incidentType;
  final VoidCallback onSaved;
  const _IncidentFormSheet({required this.incidentType, required this.onSaved});

  @override
  ConsumerState<_IncidentFormSheet> createState() => _IncidentFormSheetState();
}

class _IncidentFormSheetState extends ConsumerState<_IncidentFormSheet> {
  final _descCtrl = TextEditingController();
  bool _saving = false;

  @override
  void dispose() {
    _descCtrl.dispose();
    super.dispose();
  }

  Future<void> _save() async {
    setState(() => _saving = true);
    final db = ref.read(localDatabaseProvider);
    await db.insertDetection(
      busId: 'BUS-102',
      detectionType: widget.incidentType,
      confidence: 1.0,
      latitude: 22.5726,
      longitude: 88.3639,
      metadata: {'description': _descCtrl.text},
    );
    if (mounted) {
      Navigator.pop(context);
      widget.onSaved();
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
            content: Text('Incident queued for upload'),
            backgroundColor: Color(0xFF22C55E)),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.only(
        bottom: MediaQuery.of(context).viewInsets.bottom,
        left: 24,
        right: 24,
        top: 24,
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Text('Report: ${widget.incidentType.replaceAll("_", " ")}',
              style: const TextStyle(
                  color: Color(0xFFE8EDF5),
                  fontSize: 18,
                  fontWeight: FontWeight.w700)),
          const SizedBox(height: 16),
          TextField(
            controller: _descCtrl,
            maxLines: 3,
            style: const TextStyle(color: Color(0xFFE8EDF5)),
            decoration: InputDecoration(
              hintText: 'Describe what happened (optional)…',
              hintStyle: const TextStyle(color: Color(0xFF4D6180)),
              filled: true,
              fillColor: const Color(0xFF1A2236),
              border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(10),
                  borderSide: BorderSide.none),
            ),
          ),
          const SizedBox(height: 16),
          const Row(children: [
            Icon(Icons.location_on_rounded, color: Color(0xFF3B82F6), size: 16),
            SizedBox(width: 6),
            Text('GPS location auto-attached',
                style: TextStyle(color: Color(0xFF8FA3C0), fontSize: 12)),
          ]),
          const SizedBox(height: 20),
          ElevatedButton(
            onPressed: _saving ? null : _save,
            style: ElevatedButton.styleFrom(
              backgroundColor: const Color(0xFFEF4444),
              minimumSize: const Size.fromHeight(50),
            ),
            child: _saving
                ? const CircularProgressIndicator(
                    color: Colors.white, strokeWidth: 2)
                : const Text('Submit Report',
                    style: TextStyle(fontWeight: FontWeight.w700)),
          ),
          const SizedBox(height: 20),
        ],
      ),
    );
  }
}
