import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:camera/camera.dart';
import '../../../services/gps_service.dart';
import '../../../services/sync_service.dart';

class MonitoringScreen extends ConsumerStatefulWidget {
  const MonitoringScreen({super.key});
  @override
  ConsumerState<MonitoringScreen> createState() => _MonitoringScreenState();
}

class _MonitoringScreenState extends ConsumerState<MonitoringScreen> {
  CameraController? _cameraController;
  bool _cameraReady = false;

  static const _busId = 'mock-bus-id'; // Replace with actual bus ID from auth

  @override
  void initState() {
    super.initState();
    _initCamera();
    _startMonitoring();
  }

  Future<void> _initCamera() async {
    try {
      final cameras = await availableCameras();
      if (cameras.isEmpty) return;
      final ctrl = CameraController(
        cameras.first,
        ResolutionPreset.medium,
        enableAudio: false,
      );
      await ctrl.initialize();
      if (!mounted) return;
      setState(() {
        _cameraController = ctrl;
        _cameraReady = true;
      });
    } catch (_) {
      // Camera not available in simulator — gracefully handle
    }
  }

  Future<void> _startMonitoring() async {
    await ref.read(gpsServiceProvider).startTracking(busId: _busId);
  }

  Future<void> _stopMonitoring() async {
    await ref.read(gpsServiceProvider).stopTracking();
    if (mounted) context.pop();
  }

  @override
  void dispose() {
    _cameraController?.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final position = ref.watch(currentPositionProvider);
    final isOnline = ref.watch(networkOnlineProvider);

    return Scaffold(
      backgroundColor: Colors.black,
      body: Stack(
        children: [
          // Camera preview (full screen)
          if (_cameraReady && _cameraController != null)
            Positioned.fill(child: CameraPreview(_cameraController!))
          else
            Container(
              color: const Color(0xFF0A0F1E),
              child: const Center(
                child: Column(mainAxisSize: MainAxisSize.min, children: [
                  Icon(Icons.videocam_off_rounded, color: Color(0xFF4D6180), size: 64),
                  SizedBox(height: 12),
                  Text('Camera not available', style: TextStyle(color: Color(0xFF8FA3C0))),
                ]),
              ),
            ),

          // Top status bar
          Positioned(
            top: 0, left: 0, right: 0,
            child: Container(
              padding: EdgeInsets.only(
                top: MediaQuery.of(context).padding.top + 8,
                left: 16, right: 16, bottom: 12,
              ),
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  begin: Alignment.topCenter,
                  end: Alignment.bottomCenter,
                  colors: [Colors.black.withOpacity(0.8), Colors.transparent],
                ),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                        decoration: BoxDecoration(
                          color: const Color(0xFFEF4444).withOpacity(0.9),
                          borderRadius: BorderRadius.circular(4),
                        ),
                        child: Row(mainAxisSize: MainAxisSize.min, children: const [
                          Icon(Icons.fiber_manual_record, color: Colors.white, size: 10),
                          SizedBox(width: 4),
                          Text('AI MONITORING ACTIVE', style: TextStyle(color: Colors.white, fontSize: 11, fontWeight: FontWeight.w700, letterSpacing: 0.5)),
                        ]),
                      ),
                      const Spacer(),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                        decoration: BoxDecoration(color: Colors.black.withOpacity(0.6), borderRadius: BorderRadius.circular(6)),
                        child: Text('BUS-102', style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w700)),
                      ),
                    ],
                  ),
                  const SizedBox(height: 10),
                  Row(children: [
                    _StatusPill(label: 'GPS', active: position != null),
                    const SizedBox(width: 6),
                    _StatusPill(label: 'Camera', active: _cameraReady),
                    const SizedBox(width: 6),
                    _StatusPill(label: 'AI', active: true),
                    const SizedBox(width: 6),
                    _StatusPill(label: isOnline ? 'Online' : 'Offline', active: isOnline),
                  ]),
                  if (position != null) ...[
                    const SizedBox(height: 6),
                    Text(
                      'Speed: ${(position.speed * 3.6).toStringAsFixed(0)} km/h  |  Acc: ±${position.accuracy.toStringAsFixed(0)} m',
                      style: const TextStyle(color: Colors.white70, fontSize: 11),
                    ),
                  ],
                ],
              ),
            ),
          ),

          // Open AI Camera button
          Positioned(
            top: MediaQuery.of(context).padding.top + 70,
            right: 16,
            child: FloatingActionButton.small(
              heroTag: 'ai-btn',
              backgroundColor: const Color(0xFF3B82F6).withOpacity(0.9),
              onPressed: () => context.push('/camera'),
              child: const Icon(Icons.psychology_rounded, color: Colors.white),
            ),
          ),

          // Bottom controls
          Positioned(
            bottom: 0, left: 0, right: 0,
            child: Container(
              padding: EdgeInsets.only(
                bottom: MediaQuery.of(context).padding.bottom + 20,
                top: 20, left: 24, right: 24,
              ),
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  begin: Alignment.bottomCenter,
                  end: Alignment.topCenter,
                  colors: [Colors.black.withOpacity(0.85), Colors.transparent],
                ),
              ),
              child: SizedBox(
                height: 56,
                child: ElevatedButton.icon(
                  onPressed: _stopMonitoring,
                  icon: const Icon(Icons.stop_circle_outlined, size: 22),
                  label: const Text('STOP MONITORING', style: TextStyle(fontSize: 14, fontWeight: FontWeight.w800, letterSpacing: 1)),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFFEF4444),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _StatusPill extends StatelessWidget {
  final String label;
  final bool active;
  const _StatusPill({required this.label, required this.active});

  @override
  Widget build(BuildContext context) {
    final color = active ? const Color(0xFF22C55E) : const Color(0xFFEF4444);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: Colors.black.withOpacity(0.6),
        borderRadius: BorderRadius.circular(100),
        border: Border.all(color: color.withOpacity(0.5)),
      ),
      child: Row(mainAxisSize: MainAxisSize.min, children: [
        Container(width: 5, height: 5, decoration: BoxDecoration(color: color, shape: BoxShape.circle)),
        const SizedBox(width: 4),
        Text(label, style: TextStyle(color: color, fontSize: 10, fontWeight: FontWeight.w600)),
      ]),
    );
  }
}
