import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../core/storage/secure_storage.dart';
import '../features/auth/presentation/splash_screen.dart';
import '../features/auth/presentation/login_screen.dart';
import '../features/dashboard/presentation/driver_dashboard.dart';
import '../features/monitoring/presentation/monitoring_screen.dart';
import '../features/camera/presentation/ai_camera_screen.dart';
import '../features/detections/presentation/detection_history_screen.dart';
import '../features/incidents/presentation/incidents_screen.dart';
import '../features/map/presentation/live_map_screen.dart';
import '../features/profile/presentation/profile_screen.dart';

final routerProvider = Provider<GoRouter>((ref) {
  final secureStorage = ref.watch(secureStorageProvider);

  return GoRouter(
    initialLocation: '/',
    redirect: (context, state) async {
      final isAuth = await secureStorage.isAuthenticated();
      final isLogin = state.uri.path == '/login';
      final isSplash = state.uri.path == '/';

      if (isSplash) return null;
      if (!isAuth && !isLogin) return '/login';
      if (isAuth && isLogin) return '/dashboard';
      return null;
    },
    routes: [
      GoRoute(path: '/',         builder: (c, s) => const SplashScreen()),
      GoRoute(path: '/login',    builder: (c, s) => const LoginScreen()),
      GoRoute(path: '/dashboard', builder: (c, s) => const DriverDashboard()),
      GoRoute(path: '/monitor',  builder: (c, s) => const MonitoringScreen()),
      GoRoute(path: '/camera',   builder: (c, s) => const AiCameraScreen()),
      GoRoute(path: '/history',  builder: (c, s) => const DetectionHistoryScreen()),
      GoRoute(path: '/incidents', builder: (c, s) => const IncidentsScreen()),
      GoRoute(path: '/map',      builder: (c, s) => const LiveMapScreen()),
      GoRoute(path: '/profile',  builder: (c, s) => const ProfileScreen()),
    ],
  );
});
