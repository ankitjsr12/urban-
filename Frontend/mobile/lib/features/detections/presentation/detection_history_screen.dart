import 'package:flutter/material.dart';
import '../../../models/models.dart';

// Mock data for detection history
final _mockDetections = List.generate(20, (i) {
  final types = DetectionType.values;
  return {
    'type': types[i % types.length].name,
    'confidence': 0.75 + (i % 5) * 0.05,
    'time': '${i + 1}h ago',
    'lat': 22.57 + i * 0.001,
    'lon': 88.36 + i * 0.001,
    'synced': i % 4 != 0,
  };
});

class DetectionHistoryScreen extends StatelessWidget {
  const DetectionHistoryScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0A0F1E),
      appBar: AppBar(
        title: const Text('Detection History'),
        actions: [
          TextButton.icon(
            icon: const Icon(Icons.sync_rounded, size: 16),
            label: const Text('Sync All'),
            onPressed: () {},
          ),
        ],
      ),
      body: ListView.builder(
        padding: const EdgeInsets.all(16),
        itemCount: _mockDetections.length,
        itemBuilder: (ctx, i) {
          final d = _mockDetections[i];
          final type = d['type'] as String;
          final confidence = d['confidence'] as double;
          final synced = d['synced'] as bool;
          final color = _typeColor(type);
          return Container(
            margin: const EdgeInsets.only(bottom: 10),
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: const Color(0xFF111827),
              borderRadius: BorderRadius.circular(12),
              border: Border(left: BorderSide(color: color, width: 3)),
            ),
            child: Row(children: [
              Container(
                width: 40, height: 40,
                decoration: BoxDecoration(color: color.withOpacity(0.12), shape: BoxShape.circle),
                child: Icon(_typeIcon(type), color: color, size: 20),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  Text(type.replaceAll('_', ' '), style: const TextStyle(fontWeight: FontWeight.w700, color: Color(0xFFE8EDF5))),
                  const SizedBox(height: 3),
                  Text(
                    '${(confidence * 100).toStringAsFixed(0)}% · ${d['time']} · ${(d['lat'] as double).toStringAsFixed(4)}, ${(d['lon'] as double).toStringAsFixed(4)}',
                    style: const TextStyle(color: Color(0xFF8FA3C0), fontSize: 12),
                  ),
                ]),
              ),
              const SizedBox(width: 8),
              Icon(
                synced ? Icons.cloud_done_rounded : Icons.cloud_upload_outlined,
                color: synced ? const Color(0xFF22C55E) : const Color(0xFFF59E0B),
                size: 20,
              ),
            ]),
          );
        },
      ),
    );
  }

  Color _typeColor(String type) {
    const m = {
      'POTHOLE': Color(0xFFEF4444), 'WATERLOGGING': Color(0xFF3B82F6),
      'DAMAGED_ROAD': Color(0xFFF97316), 'VEHICLE': Color(0xFF8B5CF6),
      'PEDESTRIAN': Color(0xFFF59E0B), 'TRAFFIC_SIGN': Color(0xFF22C55E),
    };
    return m[type] ?? const Color(0xFF6B7280);
  }

  IconData _typeIcon(String type) {
    const m = {
      'POTHOLE': Icons.radio_button_checked, 'WATERLOGGING': Icons.water_drop,
      'DAMAGED_ROAD': Icons.construction, 'VEHICLE': Icons.directions_car,
      'PEDESTRIAN': Icons.directions_walk, 'TRAFFIC_SIGN': Icons.signpost,
    };
    return m[type] ?? Icons.sensors;
  }
}
