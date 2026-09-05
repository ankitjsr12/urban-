import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'app/app.dart';
import 'services/sync_service.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Firebase initialization (uncomment when google-services.json is added)
  // await Firebase.initializeApp(options: DefaultFirebaseOptions.currentPlatform);

  runApp(
    ProviderScope(
      overrides: const [],
      child: const _AppBootstrap(),
    ),
  );
}

/// Initialises background services before rendering the app.
class _AppBootstrap extends ConsumerWidget {
  const _AppBootstrap();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    // Start sync service watcher
    ref.watch(syncServiceProvider);
    return const UrbanSenseApp();
  }
}
