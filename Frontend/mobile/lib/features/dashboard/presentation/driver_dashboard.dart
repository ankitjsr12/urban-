import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../services/sync_service.dart';

class DriverDashboard extends ConsumerWidget {
  const DriverDashboard({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final isOnline = ref.watch(networkOnlineProvider);

    // Mock statistics
    const stats = [
      {'label': 'Potholes', 'value': '12', 'icon': Icons.circle, 'color': 0xFFEF4444},
      {'label': 'Waterlogging', 'value': '3', 'icon': Icons.water_drop, 'color': 0xFF3B82F6},
      {'label': 'Traffic Events', 'value': '28', 'icon': Icons.traffic, 'color': 0xFFF59E0B},
      {'label': 'Incidents', 'value': '2', 'icon': Icons.warning_rounded, 'color': 0xFFF97316},
      {'label': 'Vehicles', 'value': '341', 'icon': Icons.directions_car, 'color': 0xFF8B5CF6},
    ];

    return Scaffold(
      backgroundColor: const Color(0xFF0A0F1E),
      body: SafeArea(
        child: Column(
          children: [
            // Offline banner
            if (!isOnline)
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                color: const Color(0xFFF59E0B).withOpacity(0.15),
                child: Row(
                  children: const [
                    Icon(Icons.wifi_off_rounded, color: Color(0xFFF59E0B), size: 16),
                    SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        '🟠 OFFLINE MODE — Events will sync when connection returns',
                        style: TextStyle(color: Color(0xFFF59E0B), fontSize: 12, fontWeight: FontWeight.w600),
                      ),
                    ),
                  ],
                ),
              ),

            Expanded(
              child: SingleChildScrollView(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Bus info card
                    _BusInfoCard(),
                    const SizedBox(height: 16),

                    // Status grid
                    _StatusGrid(),
                    const SizedBox(height: 20),

                    // Today's stats
                    const Text(
                      "Today's Detections",
                      style: TextStyle(fontSize: 16, fontWeight: FontWeight.w700, color: Color(0xFFE8EDF5)),
                    ),
                    const SizedBox(height: 12),
                    GridView.count(
                      crossAxisCount: 3,
                      shrinkWrap: true,
                      physics: const NeverScrollableScrollPhysics(),
                      crossAxisSpacing: 10,
                      mainAxisSpacing: 10,
                      childAspectRatio: 1.1,
                      children: stats.map((s) => _StatTile(
                        label: s['label'] as String,
                        value: s['value'] as String,
                        icon: s['icon'] as IconData,
                        color: Color(s['color'] as int),
                      )).toList(),
                    ),
                    const SizedBox(height: 20),

                    // Main CTA
                    SizedBox(
                      width: double.infinity,
                      height: 60,
                      child: ElevatedButton.icon(
                        onPressed: () => context.push('/monitor'),
                        icon: const Icon(Icons.videocam_rounded, size: 22),
                        label: const Text(
                          'START MONITORING',
                          style: TextStyle(fontSize: 16, fontWeight: FontWeight.w800, letterSpacing: 1.5),
                        ),
                        style: ElevatedButton.styleFrom(
                          backgroundColor: const Color(0xFF3B82F6),
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                          elevation: 8,
                          shadowColor: const Color(0xFF3B82F6).withOpacity(0.4),
                        ),
                      ),
                    ),
                    const SizedBox(height: 80),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
      bottomNavigationBar: _BottomNav(currentIndex: 0),
    );
  }
}

class _BusInfoCard extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFF111827),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: const Color(0xFF1E2D45)),
        boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.3), blurRadius: 12)],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(children: [
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
              decoration: BoxDecoration(
                color: const Color(0xFF3B82F6).withOpacity(0.15),
                borderRadius: BorderRadius.circular(6),
                border: Border.all(color: const Color(0xFF3B82F6).withOpacity(0.3)),
              ),
              child: const Text('BUS-102', style: TextStyle(color: Color(0xFF3B82F6), fontWeight: FontWeight.w800, fontSize: 16)),
            ),
            const SizedBox(width: 10),
            const Text('Route: Barasat → Kolkata', style: TextStyle(color: Color(0xFF8FA3C0), fontSize: 13)),
          ]),
          const SizedBox(height: 14),
          const Divider(color: Color(0xFF1E2D45)),
          const SizedBox(height: 10),
          Row(
            children: [
              _StatusChip(label: 'GPS', active: true),
              const SizedBox(width: 8),
              _StatusChip(label: 'Camera', active: true),
              const SizedBox(width: 8),
              _StatusChip(label: 'AI', active: true),
              const SizedBox(width: 8),
              _StatusChip(label: 'Network', active: true),
            ],
          ),
        ],
      ),
    );
  }
}

class _StatusChip extends StatelessWidget {
  final String label;
  final bool active;
  const _StatusChip({required this.label, required this.active});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
      decoration: BoxDecoration(
        color: (active ? const Color(0xFF22C55E) : const Color(0xFFEF4444)).withOpacity(0.12),
        borderRadius: BorderRadius.circular(100),
        border: Border.all(color: (active ? const Color(0xFF22C55E) : const Color(0xFFEF4444)).withOpacity(0.3)),
      ),
      child: Row(mainAxisSize: MainAxisSize.min, children: [
        Container(
          width: 6, height: 6,
          decoration: BoxDecoration(
            color: active ? const Color(0xFF22C55E) : const Color(0xFFEF4444),
            shape: BoxShape.circle,
          ),
        ),
        const SizedBox(width: 5),
        Text(label, style: TextStyle(
          color: active ? const Color(0xFF22C55E) : const Color(0xFFEF4444),
          fontSize: 11, fontWeight: FontWeight.w600,
        )),
      ]),
    );
  }
}

class _StatusGrid extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Row(children: [
      Expanded(child: _InfoTile(label: 'Speed', value: '32 km/h', icon: Icons.speed_rounded, color: const Color(0xFF3B82F6))),
      const SizedBox(width: 10),
      Expanded(child: _InfoTile(label: 'Accuracy', value: '5 m', icon: Icons.gps_fixed_rounded, color: const Color(0xFF22C55E))),
    ]);
  }
}

class _InfoTile extends StatelessWidget {
  final String label, value;
  final IconData icon;
  final Color color;
  const _InfoTile({required this.label, required this.value, required this.icon, required this.color});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: const Color(0xFF111827),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: const Color(0xFF1E2D45)),
      ),
      child: Row(children: [
        Icon(icon, color: color, size: 20),
        const SizedBox(width: 10),
        Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text(label, style: const TextStyle(color: Color(0xFF8FA3C0), fontSize: 11)),
          Text(value, style: const TextStyle(color: Color(0xFFE8EDF5), fontWeight: FontWeight.w700, fontSize: 16)),
        ]),
      ]),
    );
  }
}

class _StatTile extends StatelessWidget {
  final String label, value;
  final IconData icon;
  final Color color;
  const _StatTile({required this.label, required this.value, required this.icon, required this.color});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: const Color(0xFF111827),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: const Color(0xFF1E2D45)),
      ),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(icon, color: color, size: 22),
          const SizedBox(height: 6),
          Text(value, style: TextStyle(color: color, fontSize: 20, fontWeight: FontWeight.w800)),
          Text(label, style: const TextStyle(color: Color(0xFF8FA3C0), fontSize: 10), textAlign: TextAlign.center),
        ],
      ),
    );
  }
}

class _BottomNav extends StatelessWidget {
  final int currentIndex;
  const _BottomNav({required this.currentIndex});

  @override
  Widget build(BuildContext context) {
    return BottomNavigationBar(
      currentIndex: currentIndex,
      onTap: (i) {
        final routes = ['/dashboard', '/map', '/monitor', '/incidents', '/profile'];
        if (i < routes.length) context.go(routes[i]);
      },
      items: [
        const BottomNavigationBarItem(icon: Icon(Icons.home_rounded), label: 'Home'),
        const BottomNavigationBarItem(icon: Icon(Icons.map_rounded), label: 'Map'),
        BottomNavigationBarItem(
          icon: Container(
            padding: const EdgeInsets.all(6),
            decoration: BoxDecoration(
              color: const Color(0xFF3B82F6),
              borderRadius: BorderRadius.circular(12),
            ),
            child: const Icon(Icons.videocam_rounded, color: Colors.white, size: 22),
          ),
          label: 'Monitor',
        ),
        const BottomNavigationBarItem(icon: Icon(Icons.warning_rounded), label: 'Incidents'),
        const BottomNavigationBarItem(icon: Icon(Icons.person_rounded), label: 'Profile'),
      ],
    );
  }
}
