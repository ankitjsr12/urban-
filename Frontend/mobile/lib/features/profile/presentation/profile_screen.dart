import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/storage/secure_storage.dart';
import '../../../core/storage/local_database.dart';
import '../../../services/sync_service.dart';
import '../../../core/constants/app_constants.dart';

/// Holds live profile data fetched from secure storage + local DB.
class _ProfileData {
  final String? userId;
  final String? role;
  final int pendingSync;
  const _ProfileData({this.userId, this.role, required this.pendingSync});
}

final _profileDataProvider = FutureProvider<_ProfileData>((ref) async {
  final storage = ref.watch(secureStorageProvider);
  final db = ref.watch(localDatabaseProvider);
  final userId = await storage.getUserId();
  final role = await storage.getRole();
  final pending = await db.pendingCount();
  return _ProfileData(userId: userId, role: role, pendingSync: pending);
});

/// Driver profile & account screen — uses real data from secure storage and local DB.
class ProfileScreen extends ConsumerWidget {
  const ProfileScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final profileAsync = ref.watch(_profileDataProvider);
    final isOnline = ref.watch(networkOnlineProvider);

    return Scaffold(
      backgroundColor: const Color(0xFF0A0F1E),
      appBar: AppBar(
        backgroundColor: const Color(0xFF111827),
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_rounded, color: Colors.white),
          onPressed: () => Navigator.pop(context),
        ),
        title: const Text('Driver Profile',
            style: TextStyle(color: Colors.white, fontWeight: FontWeight.w700)),
        actions: [
          // Network status pill
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 12),
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 3),
              decoration: BoxDecoration(
                color: (isOnline ? const Color(0xFF22C55E) : const Color(0xFFF59E0B))
                    .withOpacity(0.15),
                borderRadius: BorderRadius.circular(100),
                border: Border.all(
                  color: (isOnline ? const Color(0xFF22C55E) : const Color(0xFFF59E0B))
                      .withOpacity(0.3),
                ),
              ),
              child: Row(mainAxisSize: MainAxisSize.min, children: [
                Container(
                  width: 5,
                  height: 5,
                  decoration: BoxDecoration(
                    color: isOnline ? const Color(0xFF22C55E) : const Color(0xFFF59E0B),
                    shape: BoxShape.circle,
                  ),
                ),
                const SizedBox(width: 5),
                Text(
                  isOnline ? 'Online' : 'Offline',
                  style: TextStyle(
                    color: isOnline ? const Color(0xFF22C55E) : const Color(0xFFF59E0B),
                    fontSize: 11,
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ]),
            ),
          ),
        ],
      ),
      body: profileAsync.when(
        loading: () => const Center(
            child: CircularProgressIndicator(color: Color(0xFF3B82F6))),
        error: (e, _) => Center(
          child: Column(mainAxisSize: MainAxisSize.min, children: [
            const Icon(Icons.error_outline, color: Color(0xFFEF4444), size: 48),
            const SizedBox(height: 12),
            Text('Failed to load profile: $e',
                style: const TextStyle(color: Color(0xFF8FA3C0))),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: () => ref.invalidate(_profileDataProvider),
              child: const Text('Retry'),
            ),
          ]),
        ),
        data: (profile) => SingleChildScrollView(
          padding: const EdgeInsets.all(20),
          child: Column(
            children: [
              // ── Avatar & Identity ───────────────────────────────────
              Container(
                padding: const EdgeInsets.all(24),
                decoration: BoxDecoration(
                  color: const Color(0xFF111827),
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(color: const Color(0xFF1E2D45)),
                ),
                child: Column(
                  children: [
                    Container(
                      width: 80,
                      height: 80,
                      decoration: BoxDecoration(
                        gradient: const LinearGradient(
                          colors: [Color(0xFF3B82F6), Color(0xFF8B5CF6)],
                          begin: Alignment.topLeft,
                          end: Alignment.bottomRight,
                        ),
                        shape: BoxShape.circle,
                        boxShadow: [
                          BoxShadow(
                              color: const Color(0xFF3B82F6).withOpacity(0.3),
                              blurRadius: 20)
                        ],
                      ),
                      child:
                          const Icon(Icons.person_rounded, color: Colors.white, size: 44),
                    ),
                    const SizedBox(height: 16),
                    const Text('Driver Operator',
                        style: TextStyle(
                            color: Color(0xFFE8EDF5),
                            fontSize: 20,
                            fontWeight: FontWeight.w800)),
                    const SizedBox(height: 4),
                    Text(
                      profile.userId != null
                          ? 'ID: ${profile.userId!.length > 16 ? '${profile.userId!.substring(0, 16)}…' : profile.userId!}'
                          : 'Not authenticated',
                      style: const TextStyle(
                          color: Color(0xFF4D6180),
                          fontSize: 12,
                          fontFamily: 'monospace'),
                    ),
                    const SizedBox(height: 12),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 5),
                      decoration: BoxDecoration(
                        color: const Color(0xFF3B82F6).withOpacity(0.15),
                        borderRadius: BorderRadius.circular(100),
                        border: Border.all(
                            color: const Color(0xFF3B82F6).withOpacity(0.3)),
                      ),
                      child: Row(mainAxisSize: MainAxisSize.min, children: [
                        const Icon(Icons.verified_rounded,
                            color: Color(0xFF3B82F6), size: 14),
                        const SizedBox(width: 6),
                        Text(
                          profile.role ?? 'DRIVER',
                          style: const TextStyle(
                              color: Color(0xFF3B82F6),
                              fontSize: 12,
                              fontWeight: FontWeight.w700),
                        ),
                      ]),
                    ),
                  ],
                ),
              ),

              const SizedBox(height: 20),

              // ── Current Assignment ──────────────────────────────────
              _Section(
                title: 'Current Assignment',
                children: [
                  _InfoRow(
                      icon: Icons.directions_bus_rounded,
                      label: 'Bus Number',
                      value: 'BUS-102'),
                  _InfoRow(
                      icon: Icons.route_rounded,
                      label: 'Route',
                      value: 'Barasat → Esplanade'),
                  _InfoRow(
                      icon: Icons.access_time_rounded,
                      label: 'Shift',
                      value: '08:00 – 16:00'),
                  _InfoRow(
                      icon: Icons.today_rounded,
                      label: 'Date',
                      value: DateTime.now()
                          .toLocal()
                          .toString()
                          .substring(0, 10)),
                ],
              ),

              const SizedBox(height: 16),

              // ── Sync & Data Status ──────────────────────────────────
              _Section(
                title: 'Sync Status',
                children: [
                  _InfoRow(
                    icon: Icons.cloud_sync_rounded,
                    label: 'Pending Upload',
                    value: '${profile.pendingSync} event${profile.pendingSync == 1 ? '' : 's'}',
                    valueColor: profile.pendingSync > 0
                        ? const Color(0xFFF59E0B)
                        : const Color(0xFF22C55E),
                  ),
                  _InfoRow(
                    icon: isOnline
                        ? Icons.wifi_rounded
                        : Icons.wifi_off_rounded,
                    label: 'Connectivity',
                    value: isOnline ? 'Online' : 'Offline',
                    valueColor: isOnline
                        ? const Color(0xFF22C55E)
                        : const Color(0xFFF59E0B),
                  ),
                  _InfoRow(
                    icon: Icons.storage_rounded,
                    label: 'Data Mode',
                    value: AppConfig.mockMode ? 'Mock (dev)' : 'Live API',
                    valueColor: AppConfig.mockMode
                        ? const Color(0xFF8B5CF6)
                        : const Color(0xFF22C55E),
                  ),
                ],
              ),

              const SizedBox(height: 16),

              // ── App Info ─────────────────────────────────────────────
              _Section(
                title: 'Application',
                children: [
                  const _InfoRow(
                      icon: Icons.info_outline_rounded,
                      label: 'Version',
                      value: 'v1.0.0+1'),
                  _InfoRow(
                      icon: Icons.api_rounded,
                      label: 'API Endpoint',
                      value: AppConfig.mockMode
                          ? 'Mock'
                          : AppConfig.apiBaseUrl),
                ],
              ),

              const SizedBox(height: 24),

              // ── Logout ───────────────────────────────────────────────
              SizedBox(
                width: double.infinity,
                height: 52,
                child: OutlinedButton.icon(
                  onPressed: () async {
                    final confirmed = await showDialog<bool>(
                      context: context,
                      builder: (_) => AlertDialog(
                        backgroundColor: const Color(0xFF111827),
                        shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(16)),
                        title: const Text('Logout',
                            style: TextStyle(
                                color: Color(0xFFE8EDF5),
                                fontWeight: FontWeight.w700)),
                        content: const Text(
                            'Any unsynced data will remain on this device until you log back in.',
                            style: TextStyle(color: Color(0xFF8FA3C0))),
                        actions: [
                          TextButton(
                              onPressed: () => Navigator.pop(context, false),
                              child: const Text('Cancel')),
                          ElevatedButton(
                            onPressed: () => Navigator.pop(context, true),
                            style: ElevatedButton.styleFrom(
                                backgroundColor: const Color(0xFFEF4444)),
                            child: const Text('Logout'),
                          ),
                        ],
                      ),
                    );
                    if (confirmed == true) {
                      final sec = ref.read(secureStorageProvider);
                      await sec.clearAll();
                      if (context.mounted) context.go('/login');
                    }
                  },
                  icon: const Icon(Icons.logout_rounded,
                      color: Color(0xFFEF4444)),
                  label: const Text('Logout',
                      style: TextStyle(
                          color: Color(0xFFEF4444),
                          fontWeight: FontWeight.w700)),
                  style: OutlinedButton.styleFrom(
                    side: const BorderSide(color: Color(0xFFEF4444)),
                    shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(12)),
                  ),
                ),
              ),
              const SizedBox(height: 40),
            ],
          ),
        ),
      ),
    );
  }
}

// ─── Supporting Widgets ──────────────────────────────────────────────────────

class _Section extends StatelessWidget {
  final String title;
  final List<Widget> children;
  const _Section({required this.title, required this.children});

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: const Color(0xFF111827),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: const Color(0xFF1E2D45)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 14, 16, 8),
            child: Text(title,
                style: const TextStyle(
                    color: Color(0xFF4D6180),
                    fontSize: 11,
                    fontWeight: FontWeight.w700,
                    letterSpacing: 0.8)),
          ),
          ...children,
        ],
      ),
    );
  }
}

class _InfoRow extends StatelessWidget {
  final IconData icon;
  final String label, value;
  final Color? valueColor;
  const _InfoRow({
    required this.icon,
    required this.label,
    required this.value,
    this.valueColor,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
      child: Row(children: [
        Icon(icon, color: const Color(0xFF3B82F6), size: 18),
        const SizedBox(width: 12),
        Expanded(
            child: Text(label,
                style: const TextStyle(
                    color: Color(0xFF8FA3C0), fontSize: 13))),
        Flexible(
          child: Text(
            value,
            textAlign: TextAlign.end,
            style: TextStyle(
              color: valueColor ?? const Color(0xFFE8EDF5),
              fontSize: 13,
              fontWeight: FontWeight.w600,
            ),
          ),
        ),
      ]),
    );
  }
}
