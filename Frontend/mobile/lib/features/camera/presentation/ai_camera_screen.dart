import 'dart:async';
import 'dart:math';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:camera/camera.dart';
import '../../../models/models.dart';

// Mock AI detection stream — replace with real AI model or backend polling
final _detectionStreamProvider = StreamProvider<List<AiDetectionResult>>((ref) {
  return Stream.periodic(const Duration(seconds: 2), (_) {
    final rng = Random();
    final types = DetectionType.values;
    final count = rng.nextInt(3) + 1;
    return List.generate(count, (i) => AiDetectionResult(
      type: types[rng.nextInt(types.length)],
      confidence: 0.72 + rng.nextDouble() * 0.27,
      timestamp: DateTime.now(),
      bbox: [
        rng.nextDouble() * 0.5,
        rng.nextDouble() * 0.4,
        0.2 + rng.nextDouble() * 0.3,
        0.15 + rng.nextDouble() * 0.2,
      ],
    ));
  });
});

const _detectionColors = {
  DetectionType.POTHOLE:       Color(0xFFEF4444),
  DetectionType.DAMAGED_ROAD:  Color(0xFFF97316),
  DetectionType.WATERLOGGING:  Color(0xFF3B82F6),
  DetectionType.TRAFFIC_SIGN:  Color(0xFF22C55E),
  DetectionType.VEHICLE:       Color(0xFF8B5CF6),
  DetectionType.PEDESTRIAN:    Color(0xFFF59E0B),
  DetectionType.CHILD_RISK:    Color(0xFFEF4444),
  DetectionType.TRAFFIC_HAZARD: Color(0xFFF97316),
  DetectionType.ZEBRA_CROSSING: Color(0xFF14B8A6),
  DetectionType.ROAD_DIVIDER:  Color(0xFF6B7280),
};

String _detectionLabel(DetectionType t) => t.name.replaceAll('_', ' ');

class AiCameraScreen extends ConsumerStatefulWidget {
  const AiCameraScreen({super.key});
  @override
  ConsumerState<AiCameraScreen> createState() => _AiCameraScreenState();
}

class _AiCameraScreenState extends ConsumerState<AiCameraScreen> {
  CameraController? _ctrl;
  bool _ready = false;

  @override
  void initState() {
    super.initState();
    _init();
  }

  Future<void> _init() async {
    try {
      final cams = await availableCameras();
      if (cams.isEmpty) return;
      final ctrl = CameraController(cams.first, ResolutionPreset.medium, enableAudio: false);
      await ctrl.initialize();
      if (!mounted) return;
      setState(() { _ctrl = ctrl; _ready = true; });
    } catch (_) {}
  }

  @override
  void dispose() {
    _ctrl?.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final detStream = ref.watch(_detectionStreamProvider);
    final detections = detStream.valueOrNull ?? [];

    return Scaffold(
      backgroundColor: Colors.black,
      body: Stack(
        fit: StackFit.expand,
        children: [
          // Camera preview
          if (_ready && _ctrl != null)
            CameraPreview(_ctrl!)
          else
            Container(
              color: const Color(0xFF0A0F1E),
              child: const Center(child: Icon(Icons.videocam_off_rounded, color: Color(0xFF4D6180), size: 80)),
            ),

          // Bounding box overlays
          if (_ready)
            ...detections.map((det) => _BoundingBox(detection: det)),

          // Top bar
          Positioned(
            top: 0, left: 0, right: 0,
            child: Container(
              padding: EdgeInsets.only(
                top: MediaQuery.of(context).padding.top + 8,
                left: 16, right: 16, bottom: 16,
              ),
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  begin: Alignment.topCenter, end: Alignment.bottomCenter,
                  colors: [Colors.black.withOpacity(0.85), Colors.transparent],
                ),
              ),
              child: Row(children: [
                GestureDetector(
                  onTap: () => Navigator.pop(context),
                  child: Container(
                    padding: const EdgeInsets.all(8),
                    decoration: BoxDecoration(
                      color: Colors.black.withOpacity(0.6),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: const Icon(Icons.arrow_back_ios_rounded, color: Colors.white, size: 18),
                  ),
                ),
                const SizedBox(width: 12),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                  decoration: BoxDecoration(
                    color: const Color(0xFFEF4444).withOpacity(0.9),
                    borderRadius: BorderRadius.circular(4),
                  ),
                  child: Row(mainAxisSize: MainAxisSize.min, children: const [
                    Icon(Icons.fiber_manual_record, color: Colors.white, size: 8),
                    SizedBox(width: 4),
                    Text('LIVE AI', style: TextStyle(color: Colors.white, fontSize: 11, fontWeight: FontWeight.w700)),
                  ]),
                ),
                const SizedBox(width: 8),
                Text(
                  '${detections.length} detections',
                  style: const TextStyle(color: Colors.white70, fontSize: 12),
                ),
              ]),
            ),
          ),

          // Detection list overlay (bottom-left)
          Positioned(
            bottom: 24, left: 16,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisSize: MainAxisSize.min,
              children: detections.map((det) {
                final color = _detectionColors[det.type] ?? const Color(0xFF6B7280);
                return Container(
                  margin: const EdgeInsets.only(bottom: 6),
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                  decoration: BoxDecoration(
                    color: Colors.black.withOpacity(0.75),
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: color.withOpacity(0.6)),
                  ),
                  child: Row(mainAxisSize: MainAxisSize.min, children: [
                    Container(width: 8, height: 8, decoration: BoxDecoration(color: color, shape: BoxShape.circle)),
                    const SizedBox(width: 8),
                    Text(
                      '[ ${_detectionLabel(det.type)} ] ${(det.confidence * 100).toStringAsFixed(0)}%',
                      style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w700, fontSize: 13),
                    ),
                  ]),
                );
              }).toList(),
            ),
          ),
        ],
      ),
    );
  }
}

class _BoundingBox extends StatelessWidget {
  final AiDetectionResult detection;
  const _BoundingBox({required this.detection});

  @override
  Widget build(BuildContext context) {
    if (detection.bbox == null) return const SizedBox.shrink();
    final bbox = detection.bbox!;
    final color = _detectionColors[detection.type] ?? const Color(0xFF6B7280);

    return LayoutBuilder(
      builder: (ctx, constraints) {
        final w = constraints.maxWidth;
        final h = constraints.maxHeight;
        return Positioned(
          left: bbox[0] * w,
          top: bbox[1] * h,
          width: bbox[2] * w,
          height: bbox[3] * h,
          child: Container(
            decoration: BoxDecoration(
              border: Border.all(color: color, width: 2),
              borderRadius: BorderRadius.circular(4),
            ),
            child: Align(
              alignment: Alignment.topLeft,
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 2),
                color: color.withOpacity(0.8),
                child: Text(
                  '${_detectionLabel(detection.type)} ${(detection.confidence * 100).toStringAsFixed(0)}%',
                  style: const TextStyle(color: Colors.white, fontSize: 9, fontWeight: FontWeight.w700),
                ),
              ),
            ),
          ),
        );
      },
    );
  }
}
